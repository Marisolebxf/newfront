"""MySQL → techkg 图 ETL：计算专家直接关系并写入 DIRECT_RELATION 边。

直接关系判定：
1. 同机构（scholar_org_name_zh 相同）
2. 共论文（dwd_scholar_coauthor 有记录）
3. 同研究方向（research_direction 有交集）

满足任一条件即建立直接关系边。

用法：python -m script.load_direct_relation_graph
"""

from __future__ import annotations

import logging
from collections import defaultdict

from sqlalchemy import select

from db_model.scholar import DwdScholar, DwdScholarCoauthor, DwdScholarResearchDirection
from infra.graph_db import get_techkg_client
from infra.mysql import get_mysql_client

logger = logging.getLogger("script.load_direct_relation_graph")

EDGE_TYPE = "DIRECT_RELATION"


def _parse_directions(fields_text: str | None) -> set[str]:
    if not fields_text:
        return set()
    return {d.strip() for d in fields_text.replace("；", ";").split(";") if d.strip()}


def load_direct_relation_graph(batch_limit: int = 500) -> int:
    """从 MySQL 计算专家直接关系，写入图DB。返回写入边数。"""
    mysql = get_mysql_client()
    graph = get_techkg_client()
    session = mysql.session()

    try:
        # 1) 读学者信息
        scholars = list(session.execute(select(DwdScholar).limit(batch_limit)).scalars())
        scholar_map: dict[str, DwdScholar] = {s.scholar_id: s for s in scholars}
        scholar_ids = list(scholar_map.keys())

        # 2) 按机构分组
        org_groups: dict[str, list[str]] = defaultdict(list)
        for s in scholars:
            org = (s.scholar_org_name_zh or "").strip()
            if org:
                org_groups[org].append(s.scholar_id)

        # 3) 读合作关系
        coauthor_pairs: set[tuple[str, str]] = set()
        coauthors = list(
            session.execute(select(DwdScholarCoauthor).limit(batch_limit * 10)).scalars()
        )
        for ca in coauthors:
            if ca.scholar_id in scholar_map and ca.co_scholar_id in scholar_map:
                pair = tuple(sorted([ca.scholar_id, ca.co_scholar_id]))
                coauthor_pairs.add(pair)

        # 4) 读研究方向
        directions_map: dict[str, set[str]] = {}
        dirs = list(
            session.execute(select(DwdScholarResearchDirection).limit(batch_limit)).scalars()
        )
        for d in dirs:
            directions_map[d.scholar_id] = _parse_directions(d.fields)

        # 5) 计算直接关系对
        relation_pairs: dict[tuple[str, str], dict] = {}

        # 同机构
        for org, members in org_groups.items():
            if len(members) < 2:
                continue
            for i, a in enumerate(members):
                for b in members[i + 1:]:
                    pair = tuple(sorted([a, b]))
                    if pair not in relation_pairs:
                        relation_pairs[pair] = {"reasons": [], "institution": org, "directions": []}
                    if "同机构" not in relation_pairs[pair]["reasons"]:
                        relation_pairs[pair]["reasons"].append("同机构")
                    relation_pairs[pair]["institution"] = org

        # 共论文
        for pair in coauthor_pairs:
            if pair not in relation_pairs:
                relation_pairs[pair] = {"reasons": [], "institution": "", "directions": []}
            if "共论文" not in relation_pairs[pair]["reasons"]:
                relation_pairs[pair]["reasons"].append("共论文")

        # 同方向
        dir_scholar_ids = [sid for sid in scholar_ids if sid in directions_map and directions_map[sid]]
        for i, a in enumerate(dir_scholar_ids):
            for b in dir_scholar_ids[i + 1:]:
                common = directions_map[a] & directions_map[b]
                if common:
                    pair = tuple(sorted([a, b]))
                    if pair not in relation_pairs:
                        relation_pairs[pair] = {"reasons": [], "institution": "", "directions": []}
                    if "同方向" not in relation_pairs[pair]["reasons"]:
                        relation_pairs[pair]["reasons"].append("同方向")
                    relation_pairs[pair]["directions"] = list(common)[:5]

        # 6) 写入图DB
        edge_count = 0
        for (src, dst), info in relation_pairs.items():
            reasons = info["reasons"]
            strength = len(reasons) * 30 + 20  # 50-110 range
            strength = min(100, strength)

            try:
                graph.create_edge(
                    src,
                    dst,
                    edge_type=EDGE_TYPE,
                    properties={
                        "relation_subtype": "direct",
                        "reasons": "/".join(reasons),
                        "relation_strength": strength,
                        "institution": info.get("institution", ""),
                        "directions": ";".join(info.get("directions", [])),
                        "source": "etl_computed",
                    },
                )
                edge_count += 1
            except Exception as exc:  # noqa: BLE001
                logger.debug("create edge %s->%s failed: %s", src, dst, exc)

        logger.info("loaded %d DIRECT_RELATION edges", edge_count)
        return edge_count
    finally:
        session.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    count = load_direct_relation_graph()
    print(f"Done: {count} DIRECT_RELATION edges written to techkg.")
