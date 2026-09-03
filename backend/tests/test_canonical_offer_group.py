from app.services.canonical_offer_group import build_canonical_offer_groups


def _exact_product(name: str, provider: str, price: float, entity_id: str = "tc_selected_noise_max6"):
    return {
        "id": f"{provider}-sku",
        "name": name,
        "brand": "Noise",
        "matchTier": "primary",
        "matchScore": 0.97,
        "provider": provider,
        "imageUrl": f"https://{provider}.example/noise.jpg",
        "entityResolution": {
            "decision": "EXACT",
            "selected_entity": {
                "entity_id": entity_id,
                "entity_type": "PRODUCT",
                "attributes": {
                    "brand": "noise",
                    "model_signature": ["airwave", "max", "6"],
                },
            },
            "canonical_entity": {
                "entity_id": entity_id,
                "entity_type": "PRODUCT",
                "attributes": {
                    "brand": "noise",
                    "model_signature": ["airwave", "max", "6"],
                },
            },
            "provider_offer": {
                "freshness": {"observed_at": "2026-08-28T00:00:00Z"},
            },
        },
        "prices": [{"provider": provider, "price": price, "url": f"https://{provider}.example/buy"}],
    }


def test_canonical_offer_group_groups_exact_provider_offers_and_picks_lowest():
    groups = build_canonical_offer_groups(
        query="Noise Airwave Max 6 Bluetooth",
        category="Shopping",
        selected_identity={"entity_id": "tc_selected_noise_max6", "entity_type": "PRODUCT"},
        exact_results=[
            _exact_product("Noise Airwave Max 6 Bluetooth", "Amazon", 1299),
            _exact_product("Noise Airwave Max 6 Bluetooth", "Flipkart", 1199),
            _exact_product("Noise Airwave Max 6 Bluetooth", "Meesho", 1050),
        ],
        probable_results=[{"name": "Noise Airwave Max 6 maybe"}],
        related_results=[{"name": "Noise Airwave Max 2"}],
        rejected_results=[{"name": "Random earbuds"}],
        provider_status={
            "amazon": {"state": "responded"},
            "flipkart": {"state": "responded"},
            "meesho": {"state": "responded"},
            "myntra": {"state": "pending"},
        },
        resolution_mode="v3",
    )

    assert len(groups) == 1
    group = groups[0]
    assert group["best_offer"]["provider"] == "Meesho"
    assert group["best_offer"]["price"] == 1050
    assert [offer["provider"] for offer in group["offers"]] == ["Meesho", "Flipkart", "Amazon"]
    assert group["evidence_summary"]["exact_offers"] == 3
    assert group["evidence_summary"]["probable_offers"] == 1
    assert group["evidence_summary"]["related_results"] == 1
    assert group["evidence_summary"]["rejected_results"] == 1
    assert group["evidence_summary"]["authoritative"] is True


def test_canonical_offer_group_does_not_promote_probable_or_related_to_offers():
    groups = build_canonical_offer_groups(
        query="Noise Airwave Max 6 Bluetooth",
        category="Shopping",
        selected_identity={"entity_id": "tc_selected_noise_max6", "entity_type": "PRODUCT"},
        exact_results=[],
        probable_results=[_exact_product("Noise Airwave Max 6 missing proof", "CheapStore", 1)],
        related_results=[_exact_product("Noise Airwave Max 2", "Flipkart", 599)],
        rejected_results=[],
        provider_status={"flipkart": {"state": "responded"}},
        resolution_mode="v3",
    )

    assert groups == []
