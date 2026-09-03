import re
with open("backend/app/main.py", "r", encoding="utf-8") as f: content = f.read()

import_str = """
from app.graph.food_pharmacy_workflow import compile_food_pharmacy_workflow
from app.graph.transit_workflow import compile_transit_workflow
from app.graph.evaluation_workflow import compile_evaluation_workflow

food_pharmacy_workflow = compile_food_pharmacy_workflow()
transit_workflow = compile_transit_workflow()
evaluation_workflow = compile_evaluation_workflow()
"""

content = content.replace("grocery_workflow = compile_grocery_workflow()", "grocery_workflow = compile_grocery_workflow()\n" + import_str)

with open("backend/app/main.py", "w", encoding="utf-8") as f: f.write(content)
print("main.py patched.")
