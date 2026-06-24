"""科技专家论文合作关系服务：MySQL聚合 + 图数据库读写 + 分析回写。

完整流程：
1. 从 MySQL 查询两位学者的共同论文统计
2. 从图数据库查询/写入 CO_AUTHORED 边
3. 分析丰富图数据库边属性
4. 返回结构化结果 + 图谱节点给前端展示
"""

from __future__ import annotations

import json
import logging
from collections import Counter, defaultdict
from typing import Any

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from db_model.paper import DwdZhPaper, DwdZhPaperAuthor, DwdZhPaperClassification
from db_model.scholar import DwdScholar, DwdScholarCoauthor
from infra.graph_db import get_techkg_client
from infra.mysql import get_mysql_client
from service.base_module import KGModuleScaffoldService

logger = logging.getLogger(__name__)

EDGE_TYPE = "CO_AUTHORED"


class ExpertPaperCooperationService(KGModuleScaffoldService):
    module_code = "expert_paper_cooperation"

    # ---------- 主入口：分析 ----------

    def analyze(self, payload: dict[str, Any]) -> dict[str, Any]:
        expert_a_id = payload["expertAId"]
        expert_b_id = payload["expertBId"]
        start_time = payload.get("startTime")
        end_time = payload.get("endTime")

        session = get_mysql_client().session()
        try:
            # 1. 查学者基本信息
            expert_a = self._get_scholar(session, expert_a_id)
            expert_b = self._get_scholar(session, expert_b_id)

            # 2. 从 dwd_scholar_coauthor 获取合作论文数
            coauthor_info = self._get_coauthor_info(session, expert_a_id, expert_b_id)
            paper_count = coauthor_info.get("co_paper_count", 0) if coauthor_info else 0

            # 3. 从共同论文里聚合详细信息
            papers, stats = self._aggregate_shared_papers(
                session, expert_a_id, expert_b_id, start_time, end_time
            )

            # 如果聚合论文数更多，用聚合结果
            if len(papers) > paper_count:
                paper_count = len(papers)
        finally:
            session.close()

        # 4. 查/写图数据库
        graph_data = self._sync_graph(expert_a_id, expert_b_id, paper_count, stats)

        # 5. 构建结构化结果
        structured = self._build_structured_result(expert_a, expert_b, paper_count, stats)

        # 6. 构建图谱节点
        graph_nodes, graph_edges = self._build_graph_view(expert_a, expert_b, structured)

        return {
            "status": "success",
            "expertA": expert_a,
            "expertB": expert_b,
            "structuredResult": structured,
            "graphNodes": graph_nodes,
            "graphEdges": graph_edges,
        }

    # ---------- 构建图谱（写入图DB） ----------

    def build(self, payload: dict[str, Any]) -> dict[str, Any]:
        expert_a_id = payload["expertAId"]
        expert_b_id = payload["expertBId"]

        session = get_mysql_client().session()
        try:
            coauthor_info = self._get_coauthor_info(session, expert_a_id, expert_b_id)
            paper_count = coauthor_info.get("co_paper_count", 0) if coauthor_info else 0
            _, stats = self._aggregate_shared_papers(session, expert_a_id, expert_b_id, None, None)
        finally:
            session.close()

        if not paper_count and not stats.get("paper_count"):
            return {
                "status": "success",
                "edgeId": None,
                "paperCount": 0,
                "message": "未找到两人合作论文记录",
            }

        paper_count = max(paper_count, stats.get("paper_count", 0))
        graph_data = self._sync_graph(expert_a_id, expert_b_id, paper_count, stats)

        return {
            "status": "success",
            "edgeId": graph_data.get("edge_id"),
            "paperCount": paper_count,
            "message": f"已写入图数据库 CO_AUTHORED 边，合作论文 {paper_count} 篇",
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

    def _get_coauthor_info(
        self, session: Session, expert_a_id: str, expert_b_id: str
    ) -> dict[str, Any] | None:
        stmt = select(DwdScholarCoauthor).where(
            and_(
                DwdScholarCoauthor.scholar_id == expert_a_id,
                DwdScholarCoauthor.co_scholar_id == expert_b_id,
            )
        )
        row = session.execute(stmt).scalar_one_or_none()
        if row:
            return {"co_paper_count": row.co_paper_count or 0}
        # 反向查
        stmt2 = select(DwdScholarCoauthor).where(
            and_(
                DwdScholarCoauthor.scholar_id == expert_b_id,
                DwdScholarCoauthor.co_scholar_id == expert_a_id,
            )
        )
        row2 = session.execute(stmt2).scalar_one_or_none()
        if row2:
            return {"co_paper_count": row2.co_paper_count or 0}
        return None

    def _aggregate_shared_papers(
        self,
        session: Session,
        expert_a_id: str,
        expert_b_id: str,
        start_time: str | None,
        end_time: str | None,
    ) -> tuple[list[dict], dict[str, Any]]:
        """查两人共同论文（通过 paper_author JOIN），聚合统计。"""
        # 找 A 参与的论文
        stmt_a = select(DwdZhPaperAuthor.paper_id).where(
            DwdZhPaperAuthor.author_id == expert_a_id
        )
        a_paper_ids = set(session.execute(stmt_a).scalars().all())

        if not a_paper_ids:
            return [], {"paper_count": 0}

        # 找 B 也参与的论文
        stmt_b = select(DwdZhPaperAuthor.paper_id).where(
            and_(
                DwdZhPaperAuthor.author_id == expert_b_id,
                DwdZhPaperAuthor.paper_id.in_(a_paper_ids),
            )
        )
        shared_paper_ids = set(session.execute(stmt_b).scalars().all())

        if not shared_paper_ids:
            return [], {"paper_count": 0}

        # 查论文详情
        stmt_papers = select(DwdZhPaper).where(DwdZhPaper.paper_id.in_(shared_paper_ids))
        papers_raw = list(session.execute(stmt_papers).scalars())

        # 时间过滤
        start_year = int(start_time[:4]) if start_time else None
        end_year = int(end_time[:4]) if end_time else None

        papers = []
        years: list[int] = []
        topic_counter: Counter[str] = Counter()

        for p in papers_raw:
            pub_year = int(p.publication_year[:4]) if p.publication_year else None
            if start_year and pub_year and pub_year < start_year:
                continue
            if end_year and pub_year and pub_year > end_year:
                continue
            papers.append({
                "paperId": p.paper_id,
                "title": p.name_zh or p.name_en or "",
                "year": pub_year or 0,
            })
            if pub_year:
                years.append(pub_year)

        # 查关键词
        if shared_paper_ids:
            cls_stmt = select(DwdZhPaperClassification).where(
                DwdZhPaperClassification.paper_id.in_(shared_paper_ids)
            )
            for cls in session.execute(cls_stmt).scalars():
                if cls.keywords:
                    for kw in str(cls.keywords).split(";"):
                        kw = kw.strip()
                        if kw:
                            topic_counter[kw] += 1

        stats = {
            "paper_count": len(papers),
            "first_year": min(years) if years else 0,
            "last_year": max(years) if years else 0,
            "topics": [name for name, _ in topic_counter.most_common(8)],
            "representative_papers": [p["title"] for p in papers[:5]],
        }
        return papers, stats

    # ---------- 图数据库操作 ----------

    def _sync_graph(
        self,
        expert_a_id: str,
        expert_b_id: str,
        paper_count: int,
        stats: dict[str, Any],
    ) -> dict[str, Any]:
        """查图DB是否有边，没有则创建；有则更新属性（分析回写丰富图）。"""
        graph = get_techkg_client()
        topics_str = ";".join(stats.get("topics", []))

        # 计算学术影响力评分
        academic_impact = min(
            99.5,
            round(paper_count * 6.5 + len(stats.get("topics", [])) * 2.0, 1),
        )

        properties = {
            "paper_count": paper_count,
            "first_year": stats.get("first_year", 0),
            "last_year": stats.get("last_year", 0),
            "cooperation_frequency": paper_count,
            "academic_impact_score": academic_impact,
            "topics": topics_str,
            "source": "analysis",
        }

        # 查是否已有边
        try:
            existing_edges = graph.get_node_edges(
                expert_a_id, direction="out", edge_type=EDGE_TYPE, limit=100
            )
            target_edge = None
            for e in existing_edges:
                if str(e.target_id) == str(expert_b_id):
                    target_edge = e
                    break

            if target_edge:
                # 更新已有边（分析结果回写丰富图）
                graph.update_edge(str(target_edge.id), properties=properties, edge_type=EDGE_TYPE)
                return {"edge_id": str(target_edge.id), "action": "updated"}
        except Exception as exc:  # noqa: BLE001
            logger.debug("query existing edges failed: %s", exc)

        # 创建新边
        try:
            edge = graph.create_edge(
                expert_a_id, expert_b_id, edge_type=EDGE_TYPE, properties=properties
            )
            return {"edge_id": str(edge.id) if edge else None, "action": "created"}
        except Exception as exc:  # noqa: BLE001
            logger.warning("create CO_AUTHORED edge failed: %s", exc)
            return {"edge_id": None, "action": "failed"}

    # ---------- 构建结果 ----------

    def _build_structured_result(
        self,
        expert_a: dict,
        expert_b: dict,
        paper_count: int,
        stats: dict[str, Any],
    ) -> dict[str, Any]:
        first_year = stats.get("first_year", 0)
        last_year = stats.get("last_year", 0)
        topics = stats.get("topics", [])
        academic_impact = min(99.5, round(paper_count * 6.5 + len(topics) * 2.0, 1))

        shared_contribution = []
        if paper_count >= 5:
            shared_contribution.append("高水平论文产出")
        elif paper_count > 0:
            shared_contribution.append("联合论文产出")
        if expert_a.get("organization") != expert_b.get("organization"):
            shared_contribution.append("跨机构协同研究")
        if paper_count >= 3:
            shared_contribution.append("持续学术合作")

        return {
            "authorList": [expert_a["name"], expert_b["name"]],
            "authorUnits": [expert_a.get("organization", ""), expert_b.get("organization", "")],
            "paperTopics": topics[:8],
            "cooperationPaperCount": paper_count,
            "journalLevelCount": {},
            "conferenceLevelCount": {},
            "cooperationFrequency": paper_count,
            "academicImpactScore": academic_impact,
            "citation": {"total": 0, "max": 0},
            "cooperationTimeRange": {
                "startYear": first_year,
                "endYear": last_year,
                "displayText": f"{first_year} - {last_year}" if first_year and last_year else "",
            },
            "stableTeamName": f"{expert_a['name']}—{expert_b['name']}合作" if paper_count >= 3 else None,
            "stableTeamMembers": [],
            "coreCollaborators": [],
            "sharedContribution": shared_contribution,
            "representativePapers": stats.get("representative_papers", []),
        }

    def _build_graph_view(
        self, expert_a: dict, expert_b: dict, structured: dict
    ) -> tuple[list[dict], list[dict]]:
        nodes = [
            {
                "id": "expertA",
                "type": "expert",
                "label": f"专家A：{expert_a['name']}",
                "subtitle": expert_a.get("organization"),
                "x": 120, "y": 200,
                "items": [],
            },
            {
                "id": "expertB",
                "type": "expert",
                "label": f"专家B：{expert_b['name']}",
                "subtitle": expert_b.get("organization"),
                "x": 760, "y": 200,
                "items": [],
            },
            {
                "id": "paper",
                "type": "summary",
                "label": "合作论文",
                "subtitle": f"共{structured['cooperationPaperCount']}篇",
                "x": 440, "y": 80,
                "items": structured.get("representativePapers", [])[:3],
            },
            {
                "id": "topic",
                "type": "topicGroup",
                "label": "研究主题",
                "subtitle": None,
                "x": 440, "y": 360,
                "items": structured.get("paperTopics", [])[:4],
            },
        ]
        edges = [
            {"source": "expertA", "target": "paper", "label": "发表"},
            {"source": "expertB", "target": "paper", "label": "发表"},
            {"source": "paper", "target": "topic", "label": "涉及"},
            {"source": "expertA", "target": "expertB", "label": f"合作{structured['cooperationPaperCount']}篇"},
        ]
        return nodes, edges
