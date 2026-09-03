from app.services.search_intelligence import search_intelligence
from app.services.search_intelligence.models import CorrectionConfidence
from app.services.search_intelligence.relevance_classifier import classify_product_relevance, classify_products_batch


def test_grocery_packaging_words_are_not_brand_corrected() -> None:
    intent = search_intelligence("Milk Amul Gold 500 ml pouch", "Grocery")

    assert intent.corrected_query == "milk amul gold 500 ml pouch"
    assert intent.correction_confidence == CorrectionConfidence.LOW
    assert intent.show_correction_banner is False
    assert intent.parsed.brand == "Amul"
    assert intent.parsed.product_type == "milk"


def test_compact_quantity_token_is_not_treated_as_model() -> None:
    intent = search_intelligence("Amul Gold Milk 500ml", "Grocery")

    assert intent.parsed.brand == "Amul"
    assert intent.parsed.product_type == "milk"
    assert intent.parsed.model is None


def test_amul_gold_milk_relevance_rejects_other_amul_dairy_products() -> None:
    intent = search_intelligence("Amul gold milk", "Grocery")

    assert intent.parsed.brand == "Amul"
    assert intent.parsed.product_type == "milk"

    assert classify_product_relevance(intent, "Amul Gold Full Cream Milk", "Amul").value == "EXACT_INTENT"
    assert classify_product_relevance(intent, "Amul Gold Full Cream Fresh Milk Pouch", "Amul").value == "EXACT_INTENT"
    assert classify_product_relevance(intent, "Amul Lactose Free Milk (Tetra Pack)", "Amul").value == "SUBSTITUTE"
    assert classify_product_relevance(intent, "Amul Taaza Toned Fresh Milk", "Amul").value == "SUBSTITUTE"
    assert classify_product_relevance(intent, "Amul Shrikhand Elaichi", "Amul").value == "IRRELEVANT"
    assert classify_product_relevance(intent, "Amul Processed Cheese Block", "Amul").value == "IRRELEVANT"
    assert classify_product_relevance(intent, "Amul Butter", "Amul").value == "IRRELEVANT"
    assert classify_product_relevance(intent, "Amul Paneer", "Amul").value == "IRRELEVANT"


def test_query_relevance_vetoes_resolver_exact_for_wrong_amul_milk_variant() -> None:
    intent = search_intelligence("Amul gold milk", "Grocery")
    products = [
        {
            "name": "Amul Lactose Free Milk (Tetra Pack)",
            "brand": "Amul",
            "matchTier": "primary",
            "entityResolution": {"decision": "EXACT", "conflicts": []},
        },
        {
            "name": "Amul Shrikhand Elaichi",
            "brand": "Amul",
            "matchTier": "primary",
            "entityResolution": {"decision": "EXACT", "conflicts": []},
        },
    ]

    classified = classify_products_batch(intent, products)

    assert classified[0]["matchTier"] == "related"
    assert classified[0]["queryRelevance"] == "SUBSTITUTE"
    assert classified[0]["queryRelevanceNote"] == "query_relevance_vetoed_entity_resolution_exact"
    assert classified[1]["matchTier"] == "rejected"
    assert classified[1]["queryRelevance"] == "IRRELEVANT"
