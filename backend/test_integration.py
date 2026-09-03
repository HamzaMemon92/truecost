
# Integration Test - Syntax check new workflows and MCP servers
from app.graph.food_pharmacy_workflow import compile_food_pharmacy_workflow
from app.graph.transit_workflow import compile_transit_workflow
from app.graph.evaluation_workflow import compile_evaluation_workflow

from app.mcp.food_server import create_food_mcp_server
from app.mcp.pharmacy_server import create_pharmacy_mcp_server
from app.mcp.mobility_server import create_mobility_mcp_server
from app.mcp.travel_server import create_travel_mcp_server
from app.mcp.finance_server import create_finance_mcp_server
from app.mcp.productivity_server import create_productivity_mcp_server

def test_compilation():
    wf1 = compile_food_pharmacy_workflow()
    wf2 = compile_transit_workflow()
    wf3 = compile_evaluation_workflow()
    
    s1 = create_food_mcp_server()
    s2 = create_pharmacy_mcp_server()
    s3 = create_mobility_mcp_server()
    s4 = create_travel_mcp_server()
    s5 = create_finance_mcp_server()
    s6 = create_productivity_mcp_server()
    
    print("All workflows and MCP servers successfully compiled and instantiated.")

if __name__ == "__main__":
    test_compilation()
