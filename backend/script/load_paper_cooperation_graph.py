"""MySQL → techkg 图 ETL：灌 Scholar 节点与 CO_AUTHORED 合作边。

基于 dwd_scholar_coauthor 表生成合作关系写入图数据库。

用法：python -m script.load_paper_cooperation_graph
"""

from __future__ import annotations

import logging

from sqlalchemy import select

from db_model.scholar import DwdScholar, DwdScholarCoauthor
from infra.graph_db import get_techkg_client
from infra.mysql import get_mysql_client

logger = logging.getLogger("script.load_paper_cooperation_graph")

EDGE_TYPE = "CO_AUTHORED"


def load_paper_cooperation_graph(batch_limit: int = 2000) -> int:
    """从 dwd_scholar_coauthor 读取合作对，写入 CO_AUTHORED 边。返回写入边数。"""
    mysql = get_mysql_client()
    graph = get_techkg_client()

    session = mysql.session()
    try:
        # 1) 确保 Scholar 节点存在
        scholars = list(session.execute(select(DwdScholar).limit(batch_limit)).scalars())
        scholar_ids: set[str] = set()
        for s in scholars:
            vid = s.scholar_id
            scholar_ids.add(vid)
            try:
                graph.upsert_node(
                    vid,
                    labels=["Scholar"],
                    properties={
                        "scholar_id": s.scholar_id,
                        "name_zh": s.name_zh or "",
                        "name_en": s.name_en or "",
                        "scholar_org_name_zh": s.scholar_org_name_zh or "",
                        "scholar_org_name_en": s.scholar_org_name_en or "",
                        "h_index": s.h_index or 0,
                        "citation_nums": s.citation_nums or 0,
                        "paper_nums": s.paper_nums or 0,
                    },
                )
            except Exception as exc:  # noqa: BLE001
                logger.debug("upsert scholar %s failed: %s", vid, exc)

        # 2) 读合作关系
        coauthors = list(
            session.execute(select(DwdScholarCoauthor).limit(batch_limit * 5)).scalars()
        )
        edge_count = 0
        for ca in coauthors:
            src = ca.scholar_id
            dst = ca.co_scholar_id
            if not src or not dst:
                continue
            # 确保 co_scholar 节点存在（可能不在 batch 内）
            if dst not in scholar_ids:
                try:
                    graph.upsert_node(
                        dst,
                        labels=["Scholar"],
                        properties={
                            "scholar_id": dst,
                            "name_zh": ca.co_scholar_name_zh or "",
                            "name_en": ca.co_scholar_name_en or "",
                            "scholar_org_name_zh": ca.co_scholar_org_name_zh or "",
                            "scholar_org_name_en": ca.co_scholar_org_name_en or "",
                        },
                    )
                    scholar_ids.add(dst)
                except Exception:  # noqa: BLE001
                    pass

            paper_count = ca.co_paper_count or 0
            try:
                graph.create_edge(
                    src,
                    dst,
                    edge_type=EDGE_TYPE,
                    properties={
                        "paper_count": paper_count,
                        "first_year": 0,
                        "last_year": 0,
                        "cooperation_frequency": paper_count,
                        "academic_impact_score": 0.0,
                        "topics": "",
                        "source": "dwd_scholar_coauthor",
                    },
                )
                edge_count += 1
            except Exception as exc:  # noqa: BLE001
                logger.debug("create edge %s->%s failed: %s", src, dst, exc)

        logger.info("loaded %d CO_AUTHORED edges", edge_count)
        return edge_count
    finally:
        session.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    count = load_paper_cooperation_graph()
    print(f"Done: {count} CO_AUTHORED edges written to techkg.")
