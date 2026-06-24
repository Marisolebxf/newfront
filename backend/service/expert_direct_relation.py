"""科技专家直接关系服务：MySQL分析 + 图数据库读写。

完整流程：
1. 从 MySQL 查两位学者信息，判定直接关系依据（同机构/共论文/同方向）
2. 从图数据库查询/写入 DIRECT_RELATION 边
3. 分析结果回写丰富图数据库
4. 返回结构化结果 + 图谱节点给前端
"""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from db_model.scholar import DwdScholar, DwdScholarCoauthor, DwdScholarResearchDirection
from infra.graph_db import get_techkg_client
from infra.mysql import get_mysql_client
from service.base_module import KGModuleScaffoldService

logger = logging.getLogger(__name__)

EDGE_TYPE = "DIRECT_RELATION"


def _parse_directions(fields_text: str | None) -> list[str]:
    if not fields_text:
        return []
    return [d.strip() for d in fields_text.replace("；", ";").split(";") if d.strip()]


class ExpertDirectRelationService(KGModuleScaffoldService):
    module_code = "expert_direct_relation"

    def analyze(self, payload: dict[str, Any]) -> dict[str, Any]:
        expert_a_id = payload["expertAId"]
        expert_b_id = payload["expertBId"]

        session = get_mysql_client().session()
        try:
            expert_a = self._get_scholar(session, expert_a_id)
            expert_b = self._get_scholar(session, expert_b_id)
            reasons, institution, directions = self._compute_relation(
                session, expert_a_id, expert_b_id, expert_a, expert_b
            )
        finally:
            session.close()

        strength = min(100, len(reasons) * 30 + 20)

        # 同步图数据库
        graph_data = self._sync_graph(
            expert_a_id, expert_b_id, reasons, strength, institution, directions
        )

        relation = {
            "reasons": reasons,
            "relationStrength": strength,
            "institution": institution,
            "directions": directions,
        }

        graph_nodes, graph_edges = self._build_graph_view(expert_a, expert_b, relation)

        return {
            "status": "success",
            "expertA": expert_a,
            "expertB": expert_b,
            "relation": relation,
            "graphNodes": graph_nodes,
            "graphEdges": graph_edges,
        }

    def build(self, payload: dict[str, Any]) -> dict[str, Any]:
        expert_a_id = payload["expertAId"]
        expert_b_id = payload["expertBId"]

        session = get_mysql_client().session()
        try:
            expert_a = self._get_scholar(session, expert_a_id)
            expert_b = self._get_scholar(session, expert_b_id)
            reasons, institution, directions = self._compute_relation(
                session, expert_a_id, expert_b_id, expert_a, expert_b
            )
        finally:
            session.close()

        if not reasons:
            return {
                "status": "success",
                "edgeId": None,
                "relationStrength": 0,
                "reasons": [],
                "message": "未发现两人之间的直接关系依据",
            }

        strength = min(100, len(reasons) * 30 + 20)
        graph_data = self._sync_graph(
            expert_a_id, expert_b_id, reasons, strength, institution, directions
        )

        return {
            "status": "success",
            "edgeId": graph_data.get("edge_id"),
            "relationStrength": strength,
            "reasons": reasons,
            "message": f"已写入图数据库 DIRECT_RELATION 边，关系强度 {strength}",
        }

    # ---------- MySQL 查询 ----------

    def _get_scholar(self, session: Session, scholar_id: str) -> dict[str, Any]:
        scholar = session.get(DwdScholar, scholar_id)
        if not scholar:
            raise KeyError(f"学者不存在: {scholar_id}")
        return {
            "expertId": scholar.scholar_id,
            "name": scholar.name_zh or scholar.name_en or scholar.scholar_id,
            "organization": scholar.scholar_org_name_zh or scholar.scholar_org_name_en or "",
            "paperCount": scholar.paper_nums or 0,
            "citationCount": scholar.citation_nums or 0,
            "hIndex": float(scholar.h_index or 0),
        }

    def _compute_relation(
        self,
        session: Session,
        expert_a_id: str,
        expert_b_id: str,
        expert_a: dict,
        expert_b: dict,
    ) -> tuple[list[str], str, list[str]]:
        """计算直接关系的依据。返回 (reasons, institution, common_directions)。"""
        reasons: list[str] = []
        institution = ""
        common_directions: list[str] = []

        # 同机构
        org_a = expert_a.get("organization", "").strip()
        org_b = expert_b.get("organization", "").strip()
        if org_a and org_b and org_a == org_b:
            reasons.append("同机构")
            institution = org_a

        # 共论文
        stmt = select(DwdScholarCoauthor).where(
            and_(
                DwdScholarCoauthor.scholar_id == expert_a_id,
                DwdScholarCoauthor.co_scholar_id == expert_b_id,
            )
        )
        coauthor = session.execute(stmt).scalar_one_or_none()
        if not coauthor:
            stmt2 = select(DwdScholarCoauthor).where(
                and_(
                    DwdScholarCoauthor.scholar_id == expert_b_id,
                    DwdScholarCoauthor.co_scholar_id == expert_a_id,
                )
            )
            coauthor = session.execute(stmt2).scalar_one_or_none()
        if coauthor:
            reasons.append("共论文")

        # 同研究方向
        dir_a_row = session.get(DwdScholarResearchDirection, expert_a_id)
        dir_b_row = session.get(DwdScholarResearchDirection, expert_b_id)
        dirs_a = set(_parse_directions(dir_a_row.fields if dir_a_row else None))
        dirs_b = set(_parse_directions(dir_b_row.fields if dir_b_row else None))
        common = dirs_a & dirs_b
        if common:
            reasons.append("同方向")
            common_directions = list(common)[:5]

        return reasons, institution, common_directions

    # ---------- 图数据库操作 ----------

    def _sync_graph(
        self,
        expert_a_id: str,
        expert_b_id: str,
        reasons: list[str],
        strength: int,
        institution: str,
        directions: list[str],
    ) -> dict[str, Any]:
        graph = get_techkg_client()
        properties = {
            "relation_subtype": "direct",
            "reasons": "/".join(reasons),
            "relation_strength": strength,
            "institution": institution,
            "directions": ";".join(directions),
            "source": "analysis",
        }

        # 查已有边
        try:
            existing_edges = graph.get_node_edges(
                expert_a_id, direction="out", edge_type=EDGE_TYPE, limit=50
            )
            for e in existing_edges:
                if str(e.target_id) == str(expert_b_id):
                    graph.update_edge(str(e.id), properties=properties, edge_type=EDGE_TYPE)
                    return {"edge_id": str(e.id), "action": "updated"}
        except Exception as exc:  # noqa: BLE001
            logger.debug("query existing edges failed: %s", exc)

        # 创建新边
        if not reasons:
            return {"edge_id": None, "action": "skip"}
        try:
            edge = graph.create_edge(
                expert_a_id, expert_b_id, edge_type=EDGE_TYPE, properties=properties
            )
            return {"edge_id": str(edge.id) if edge else None, "action": "created"}
        except Exception as exc:  # noqa: BLE001
            logger.warning("create DIRECT_RELATION edge failed: %s", exc)
            return {"edge_id": None, "action": "failed"}

    # ---------- 构建图谱视图 ----------

    def _build_graph_view(
        self, expert_a: dict, expert_b: dict, relation: dict
    ) -> tuple[list[dict], list[dict]]:
        reasons = relation.get("reasons", [])
        strength = relation.get("relationStrength", 0)
        directions = relation.get("directions", [])

        nodes = [
            {
                "id": "expertA",
                "type": "expert",
                "label": f"专家A：{expert_a['name']}",
                "subtitle": expert_a.get("organization"),
                "x": 150, "y": 300,
            },
            {
                "id": "expertB",
                "type": "expert",
                "label": f"专家B：{expert_b['name']}",
                "subtitle": expert_b.get("organization"),
                "x": 750, "y": 300,
            },
        ]

        # 关系原因作为中间节点
        if "同机构" in reasons:
            nodes.append({
                "id": "institution",
                "type": "info",
                "label": f"机构：{relation.get('institution', '')}",
                "subtitle": "同机构",
                "x": 450, "y": 150,
            })
        if "共论文" in reasons:
            nodes.append({
                "id": "copaper",
                "type": "info",
                "label": "共同论文",
                "subtitle": "合作发表",
                "x": 450, "y": 450,
            })
        if directions:
            nodes.append({
                "id": "direction",
                "type": "info",
                "label": "研究方向",
                "subtitle": "、".join(directions[:3]),
                "x": 450, "y": 300,
            })

        edges = [
            {"source": "expertA", "target": "expertB", "label": f"直接关系（强度{strength}）"},
        ]
        if "同机构" in reasons:
            edges.append({"source": "expertA", "target": "institution", "label": "任职"})
            edges.append({"source": "expertB", "target": "institution", "label": "任职"})
        if "共论文" in reasons:
            edges.append({"source": "expertA", "target": "copaper", "label": "发表"})
            edges.append({"source": "expertB", "target": "copaper", "label": "发表"})

        return nodes, edges
