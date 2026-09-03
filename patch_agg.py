import re

with open("backend/app/api/endpoints/aggregator.py", "r", encoding="utf-8") as f:
    content = f.read()

if "compile_food_pharmacy_workflow" not in content:
    import_str = """
from app.graph.food_pharmacy_workflow import compile_food_pharmacy_workflow
from app.graph.evaluation_workflow import compile_evaluation_workflow

food_pharmacy_workflow = compile_food_pharmacy_workflow()
evaluation_workflow = compile_evaluation_workflow()

class GeneralSearchRequest(BaseModel):
    query: str
    category: str
    location: Optional[str] = None

@router.post("/search")
async def general_search(req: GeneralSearchRequest):
    # Unified search endpoint
    try:
        if req.category in ["food", "pharmacy"]:
            state = {"query": req.query, "category": req.category, "items": [], "ranked_options": [], "errors": []}
            result = await food_pharmacy_workflow.ainvoke(state)
            return {"status": "success", "engine": "food_pharmacy_workflow", "results": result.get("ranked_options", [])}
        elif req.category in ["finance", "services", "productivity"]:
            state = {"requirements": req.query, "domain": req.category, "candidates": [], "comparison_matrix": {}}
            result = await evaluation_workflow.ainvoke(state)
            return {"status": "success", "engine": "evaluation_workflow", "results": result.get("comparison_matrix", {})}
        else:
            raise HTTPException(status_code=400, detail="Category not supported in general search. Use specific endpoints.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
"""
    content = content + import_str
    with open("backend/app/api/endpoints/aggregator.py", "w", encoding="utf-8") as f:
        f.write(content)
    print("aggregator.py patched.")
else:
    print("aggregator.py already patched.")
