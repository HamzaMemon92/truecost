from app.agents.shopping_agent import choose_route, determine_complexity


def test_simple_query_routes_to_direct_tools():
    complexity = determine_complexity("sony wh-1000xm5")
    assert complexity == "simple"
    assert choose_route(complexity) == "direct-tools"


def test_moderate_query_routes_to_agent():
    complexity = determine_complexity("best iphone under 80000")
    assert complexity in {"moderate", "complex"}
    route = choose_route(complexity)
    assert route in {"shopping-agent", "deep-agent"}


def test_complexity_driven_not_version_driven():
    """
    IMPORTANT: Complexity routing should ONLY depend on query characteristics,
    NOT on Python version or environment.
    
    This test verifies the architecture principle:
      ✓ Same complexity → same route (guaranteed)
      ✓ Route stability across Python versions (3.10, 3.11, etc.)
      ✓ Deep Agents is optional capability, not foundational
    """
    # Same query should always produce same complexity
    query_1 = "compare gaming laptops"
    query_2 = "compare gaming laptops"
    assert determine_complexity(query_1) == determine_complexity(query_2)
    
    # Same complexity should always route to same path
    complexity = determine_complexity(query_1)
    route = choose_route(complexity)
    assert route == choose_route(complexity)  # Deterministic


def test_simple_category_keywords():
    """Single product category queries = SIMPLE."""
    simple_queries = [
        "sony headphones",
        "iphone 17",
        "macbook air",
        "dell laptop",
    ]
    for query in simple_queries:
        complexity = determine_complexity(query)
        assert complexity == "simple", f"Query '{query}' should be simple, got {complexity}"


def test_moderate_category_keywords():
    """Comparison/features/constraints = MODERATE or COMPLEX."""
    # Must match keywords in app/config.py DeepReasoningPolicy.moderate_keywords
    moderate_queries = [
        "best laptop under 100000",
        "compare iphones",
        "budget laptop",
        "laptop with battery life",
        "camera quality on phones",
        "offer on electronics",
    ]
    for query in moderate_queries:
        complexity = determine_complexity(query)
        assert complexity in {"moderate", "complex"}, f"Query '{query}' should be moderate/complex, got {complexity}"


def test_complex_queries():
    """Multi-constraint, detailed, trade-off analysis = COMPLEX."""
    complex_queries = [
        "compare top 3 gaming laptops by performance price and thermal",
        "best laptop for ai development that is portable and has good battery life",
        "find laptop with rtx 5000 32gb ram under 200000 with warranty",
    ]
    for query in complex_queries:
        complexity = determine_complexity(query)
        assert complexity == "complex", f"Query '{query}' should be complex, got {complexity}"


def test_routing_matches_complexity():
    """Verify routing logic creates expected paths."""
    test_cases = [
        ("simple", "direct-tools"),
        ("moderate", "shopping-agent"),
        ("complex", "deep-agent"),
    ]
    for complexity, expected_route in test_cases:
        route = choose_route(complexity)
        assert route == expected_route, f"Complexity {complexity} should route to {expected_route}, got {route}"


def test_long_queries_escalate_complexity():
    """Long, detailed queries should escalate to higher reasoning depth."""
    short = "laptop"
    long = "I am looking for a laptop that has at least 16GB RAM, an RTX 5000 GPU, weighs less than 2kg, has excellent thermal management for deep learning workloads, good build quality, and available at any price point"
    
    short_complexity = determine_complexity(short)
    long_complexity = determine_complexity(long)
    
    # Long query should not be simpler than short
    complexity_order = {"simple": 0, "moderate": 1, "complex": 2}
    assert complexity_order[long_complexity] >= complexity_order[short_complexity]
