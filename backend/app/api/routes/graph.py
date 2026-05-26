from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from neo4j import GraphDatabase
from app.core.config import settings
from app.models.schemas import DetectedComponent, Relation

router = APIRouter()

_driver = None

def get_driver():
    global _driver
    if _driver is None:
        _driver = GraphDatabase.driver(settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password))
    return _driver

class GraphRequest(BaseModel):
    image_id: str
    components: List[DetectedComponent]
    relations: List[Relation]

@router.post("/save")
async def save_graph(req: GraphRequest):
    try:
        with get_driver().session() as session:
            session.run(
                "MATCH (n {image_id: $image_id}) DETACH DELETE n",
                image_id=req.image_id
            )
            session.run(
                """
                UNWIND $components AS comp
                MERGE (c:Component {id: comp.id, image_id: $image_id})
                SET c.type = comp.type, c.bbox = comp.bbox
                """,
                components=[{"id": c.id, "type": c.type, "bbox": c.bbox} for c in req.components],
                image_id=req.image_id
            )
            session.run(
                """
                UNWIND $relations AS rel
                MATCH (a:Component {id: rel.subject, image_id: $image_id})
                MERGE (b:Component {id: rel.object, image_id: $image_id})
                ON CREATE SET b.type = "external", b.image_id = $image_id
                MERGE (a)-[r:CONNECTS {relation: rel.relation}]->(b)
                """,
                relations=[{"subject": r.subject, "object": r.object, "relation": r.relation} for r in req.relations],
                image_id=req.image_id
            )
        return {"status": "ok", "message": f"已寫入 {len(req.components)} 個節點，{len(req.relations)} 條關係"}
    except Exception as e:
        raise HTTPException(500, f"Neo4j 寫入失敗：{e}")


@router.get("/query/{image_id}")
async def query_graph(image_id: str):
    try:
        with get_driver().session() as session:
            result = session.run(
                """
                MATCH (a:Component {image_id: $image_id})-[r]->(b)
                RETURN a.id, a.type, r.relation, b.id, b.type
                """,
                image_id=image_id
            )
            edges = [{"from": r["a.id"], "relation": r["r.relation"], "to": r["b.id"]} for r in result]
        return {"image_id": image_id, "edges": edges}
    except Exception as e:
        raise HTTPException(500, f"Neo4j 查詢失敗：{e}")
