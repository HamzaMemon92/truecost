from app.services.canonical_offer_group import build_canonical_offer_groups


def _status_by_provider_key(group: dict) -> dict:
    def key(provider: str) -> str:
        provider = provider.casefold()
        if "bigbasket" in provider or "big basket" in provider:
            return "bigbasket"
        if "swiggy" in provider or "instamart" in provider:
            return "swiggy"
        if "blinkit" in provider:
            return "blinkit"
        if "zepto" in provider:
            return "zepto"
        return provider

    return {key(provider): status for provider, status in group["provider_status"].items()}


def _exact_product(
    product_id: str,
    title: str,
    entity_id: str,
    provider: str,
    price: float,
    weight: str = "500 ml",
    image_url: str = "",
    image_match_status: str | None = None,
) -> dict:
    unknown_attributes = {}
    if image_match_status is not None:
        unknown_attributes = {
            "image_match_status": image_match_status,
            "image_source_provider": provider,
            "image_source_product_id": product_id,
            "image_source_variant_id": product_id,
        }
    return {
        "id": product_id,
        "name": title,
        "brand": "Amul",
        "category": "Grocery",
        "weightVolume": weight,
        "imageUrl": image_url,
        "providerSku": product_id,
        "unknownAttributes": unknown_attributes,
        "matchTier": "primary",
        "matchScore": 0.86,
        "entityResolution": {
            "selected_entity": {
                "entity_id": "selected-amul-milk",
                "attributes": {"brand": "amul", "product_signature": "milk"},
            },
            "canonical_entity": {
                "entity_id": "selected-amul-milk",
                "attributes": {"brand": "amul", "product_signature": "milk"},
            },
            "candidate_entity": {
                "entity_id": entity_id,
                "attributes": {"brand": "amul", "product_signature": title.casefold()},
            },
        },
        "prices": [{"provider": provider, "price": price}],
    }


def test_canonical_groups_use_candidate_identity_not_vague_selected_query_identity() -> None:
    groups = build_canonical_offer_groups(
        query="Amul milk",
        category="Grocery",
        selected_identity={"entity_id": "selected-amul-milk", "attributes": {"brand": "amul"}},
        exact_results=[
            _exact_product("gold-bb", "Gold Full Cream Milk", "amul-gold-500ml", "BigBasket", 32),
            _exact_product("gold-zepto", "Amul Gold Full Cream Milk Pouch", "amul-gold-500ml", "Zepto", 35),
            _exact_product("taaza-bb", "Taaza Milk", "amul-taaza-500ml", "BigBasket", 27),
        ],
        related_results=[],
        rejected_results=[],
        provider_status={},
    )

    assert len(groups) == 2
    by_entity = {group["entity"]["entity_id"]: group for group in groups}
    assert {offer["provider"] for offer in by_entity["amul-gold-500ml"]["offers"]} == {"BigBasket", "Zepto"}
    assert {offer["provider"] for offer in by_entity["amul-taaza-500ml"]["offers"]} == {"BigBasket"}


def test_canonical_groups_dedupe_repeated_provider_offers() -> None:
    duplicate = _exact_product("gold-bb", "Gold Full Cream Milk", "amul-gold-500ml", "BigBasket", 32)
    groups = build_canonical_offer_groups(
        query="Amul milk",
        category="Grocery",
        selected_identity={"entity_id": "selected-amul-milk"},
        exact_results=[duplicate, duplicate],
        related_results=[],
        rejected_results=[],
        provider_status={},
    )

    assert len(groups) == 1
    assert len(groups[0]["offers"]) == 1


def test_broad_amul_milk_ranks_regular_pouch_before_specialty_milk() -> None:
    groups = build_canonical_offer_groups(
        query="Amul milk",
        category="Grocery",
        selected_identity={"entity_id": "selected-amul-milk", "attributes": {"brand": "amul"}},
        exact_results=[
            _exact_product("buffalo-bb", "Buffalo Milk", "buffalo-milk", "BigBasket", 40),
            _exact_product("spray-bb", "Amul Spray Infant Milk Food", "amul-spray", "BigBasket", 255),
            _exact_product("rose-swiggy", "Amul Kool Milk - Rose Flavour", "amul-kool-rose", "Swiggy Instamart", 20),
            _exact_product("gold-bb", "Amul Gold Full Cream Fresh Milk Pouch", "amul-gold-500ml", "BigBasket", 32),
            _exact_product("gold-zepto", "Amul Gold Full Cream Fresh Milk Pouch", "amul-gold-500ml", "Zepto", 35),
            _exact_product("taaza-bb", "Amul Taaza Toned Fresh Milk Pouch", "amul-taaza-500ml", "BigBasket", 27),
            _exact_product("lactose-zepto", "Amul Lactose Free Milk", "amul-lactose-free", "Zepto", 24),
        ],
        related_results=[],
        rejected_results=[],
        provider_status={},
    )

    assert groups[0]["entity"]["entity_id"] == "amul-gold-500ml"
    assert "Gold" in groups[0]["title"]
    assert groups[1]["entity"]["entity_id"] == "amul-taaza-500ml"
    assert [group["entity"]["entity_id"] for group in groups[:2]] == ["amul-gold-500ml", "amul-taaza-500ml"]
    assert groups[-1]["entity"]["entity_id"] == "buffalo-milk"


def test_canonical_groups_dedupe_same_provider_same_title_weight_even_with_different_ids() -> None:
    first = _exact_product("zepto-a", "Amul Lactose Free Milk", "amul-lactose-180ml", "Zepto", 24)
    second = _exact_product("zepto-b", "Amul Lactose Free Milk", "amul-lactose-180ml", "Zepto", 25)

    groups = build_canonical_offer_groups(
        query="Amul milk",
        category="Grocery",
        selected_identity={"entity_id": "selected-amul-milk"},
        exact_results=[first, second],
        related_results=[],
        rejected_results=[],
        provider_status={},
    )

    assert len(groups) == 1
    assert len(groups[0]["offers"]) == 1
    assert groups[0]["offers"][0]["price"] == 24


def test_canonical_groups_do_not_compare_different_pack_sizes() -> None:
    groups = build_canonical_offer_groups(
        query="Amul milk",
        category="Grocery",
        selected_identity={"entity_id": "selected-amul-milk"},
        exact_results=[
            _exact_product("taaza-200", "Amul Taaza Homogenised Toned Milk", "amul-taaza", "Zepto", 17, "1 pack (200 ml)"),
            _exact_product("taaza-500", "Amul Taaza Toned Fresh Milk Pouch", "amul-taaza", "BigBasket", 27, "500 ml"),
            _exact_product("taaza-1l", "Amul Taaza Homogenised Toned Milk", "amul-taaza", "BigBasket", 77, "1 L"),
        ],
        related_results=[],
        rejected_results=[],
        provider_status={},
    )

    assert len(groups) == 3
    offer_weights = [
        {offer["product"]["weightVolume"] for offer in group["offers"]}
        for group in groups
    ]
    assert {"1 pack (200 ml)"} in offer_weights
    assert {"500 ml"} in offer_weights
    assert {"1 L"} in offer_weights


def test_canonical_groups_compare_litre_synonyms() -> None:
    groups = build_canonical_offer_groups(
        query="Amul gold milk",
        category="Grocery",
        selected_identity={"entity_id": "selected-amul-gold-milk"},
        exact_results=[
            _exact_product(
                "gold-swiggy-1ltr",
                "Amul Gold Homogenised Standardised Full Cream Milk",
                "amul-gold-full-cream",
                "Swiggy Instamart",
                83,
                "1 ltr",
            ),
            _exact_product(
                "gold-bb-1l",
                "Gold Homogenised Standardised Milk",
                "amul-gold-full-cream",
                "BigBasket",
                83,
                "1 L",
            ),
        ],
        related_results=[],
        rejected_results=[],
        provider_status={},
    )

    assert len(groups) == 1
    assert {offer["provider"] for offer in groups[0]["offers"]} == {"Swiggy Instamart", "BigBasket"}


def test_canonical_groups_do_not_compare_single_litre_with_multipack_litre() -> None:
    groups = build_canonical_offer_groups(
        query="Amul gold milk",
        category="Grocery",
        selected_identity={"entity_id": "selected-amul-gold-milk"},
        exact_results=[
            _exact_product(
                "gold-swiggy-1ltr-x12",
                "Amul Gold Homogenised Standardised Full Cream Milk",
                "amul-gold-full-cream",
                "Swiggy Instamart",
                996,
                "1 ltr x 12",
            ),
            _exact_product(
                "gold-bb-1l",
                "Gold Homogenised Standardised Milk",
                "amul-gold-full-cream",
                "BigBasket",
                83,
                "1 L",
            ),
        ],
        related_results=[],
        rejected_results=[],
        provider_status={},
    )

    assert len(groups) == 2
    offer_weights = [
        {offer["product"]["weightVolume"] for offer in group["offers"]}
        for group in groups
    ]
    assert {"1 ltr x 12"} in offer_weights
    assert {"1 L"} in offer_weights


def test_canonical_group_provider_status_is_scoped_to_this_product_group() -> None:
    groups = build_canonical_offer_groups(
        query="Amul gold milk",
        category="Grocery",
        selected_identity={"entity_id": "selected-amul-gold-milk"},
        exact_results=[
            _exact_product("gold-bb-500", "Gold Full Cream Milk", "amul-gold-500ml", "BigBasket", 32, "500 ml"),
            _exact_product("gold-zepto-500", "Gold Full Cream Milk", "amul-gold-500ml", "Zepto", 34, "500 ml"),
            _exact_product(
                "gold-swiggy-1l",
                "Amul Gold Homogenised Standardised Full Cream Milk",
                "amul-gold-1l",
                "Swiggy Instamart",
                83,
                "1 ltr",
            ),
        ],
        related_results=[],
        rejected_results=[],
        provider_status={
            "bigbasket": {"state": "responded", "exact_matches": 2},
            "zepto": {"state": "responded", "exact_matches": 1},
            "swiggy": {"state": "responded", "exact_matches": 1},
            "blinkit": {"state": "timeout"},
        },
    )

    by_weight = {
        next(iter({offer["product"]["weightVolume"] for offer in group["offers"]})): group
        for group in groups
    }
    five_hundred_status = _status_by_provider_key(by_weight["500 ml"])
    assert five_hundred_status["bigbasket"]["exact_matches"] == 1
    assert five_hundred_status["zepto"]["exact_matches"] == 1
    assert five_hundred_status["swiggy"]["exact_matches"] == 0
    assert five_hundred_status["swiggy"]["match_status"] == "no_match"
    assert five_hundred_status["blinkit"]["state"] == "timeout"

    one_litre_status = _status_by_provider_key(by_weight["1 ltr"])
    assert one_litre_status["swiggy"]["exact_matches"] == 1
    assert one_litre_status["bigbasket"]["exact_matches"] == 0


def test_canonical_groups_merge_provider_wording_differences_for_specific_grocery_sku() -> None:
    selected_identity = {
        "entity_id": "selected-amul-gold-500ml",
        "attributes": {"brand": "amul", "product_signature": ["gold", "milk"]},
    }
    groups = build_canonical_offer_groups(
        query="Amul gold milk",
        category="Grocery",
        selected_identity=selected_identity,
        exact_results=[
            {
                **_exact_product(
                    "zepto-gold-500ml",
                    "Amul Gold Full Cream Fresh Milk | Pouch",
                    "zepto-rich-title",
                    "Zepto",
                    34,
                    "500 ml",
                ),
                "entityResolution": {
                    "decision": "EXACT",
                    "selected_entity": selected_identity,
                    "candidate_entity": {
                        "entity_id": "zepto-rich-title",
                        "attributes": {"brand": "amul", "product_signature": ["gold", "milk", "full", "cream", "fresh", "pouch"]},
                    },
                },
            },
            {
                **_exact_product(
                    "swiggy-gold-500ml",
                    "Amul Gold Pasteurised Full Cream Milk",
                    "swiggy-rich-title",
                    "Swiggy Instamart",
                    36,
                    "500 ml",
                ),
                "entityResolution": {
                    "decision": "EXACT",
                    "selected_entity": selected_identity,
                    "candidate_entity": {
                        "entity_id": "swiggy-rich-title",
                        "attributes": {"brand": "amul", "product_signature": ["gold", "milk", "pasteurised", "full", "cream"]},
                    },
                },
            },
            {
                **_exact_product(
                    "swiggy-gold-1l",
                    "Amul Gold Homogenised Standardised Full Cream Milk",
                    "swiggy-rich-title",
                    "Swiggy Instamart",
                    83,
                    "1 ltr",
                ),
                "entityResolution": {
                    "decision": "EXACT",
                    "selected_entity": selected_identity,
                    "candidate_entity": {
                        "entity_id": "swiggy-rich-title",
                        "attributes": {"brand": "amul", "product_signature": ["gold", "milk", "homogenised", "standardised", "full", "cream"]},
                    },
                },
            },
        ],
        related_results=[
            _exact_product("taaza-500ml", "Amul Taaza Milky Milk", "amul-taaza-500ml", "BigBasket", 29, "500 ml")
        ],
        rejected_results=[],
        provider_status={
            "zepto": {"state": "responded"},
            "swiggy": {"state": "responded"},
            "bigbasket": {"state": "responded"},
            "blinkit": {"state": "timeout"},
        },
    )

    five_hundred = next(group for group in groups if {offer["product"]["weightVolume"] for offer in group["offers"]} == {"500 ml"})
    assert {offer["provider"] for offer in five_hundred["offers"]} == {"Zepto", "Swiggy Instamart"}
    assert {offer["price"] for offer in five_hundred["offers"]} == {34, 36}
    status = _status_by_provider_key(five_hundred)
    assert status["swiggy"]["exact_matches"] == 1
    assert status["bigbasket"]["match_status"] == "no_match"
    assert status["blinkit"]["state"] == "timeout"

    one_litre = next(group for group in groups if {offer["product"]["weightVolume"] for offer in group["offers"]} == {"1 ltr"})
    assert {offer["provider"] for offer in one_litre["offers"]} == {"Swiggy Instamart"}


def test_canonical_group_images_stay_bound_to_their_sku_size() -> None:
    groups = build_canonical_offer_groups(
        query="Amul gold milk",
        category="Grocery",
        selected_identity={"entity_id": "selected-amul-gold-milk"},
        exact_results=[
            _exact_product(
                "gold-500ml-bb",
                "Amul Gold Full Cream Milk Pouch",
                "amul-gold-full-cream",
                "BigBasket",
                32,
                "500 ml",
                "https://cdn.test/amul-gold-500ml-pouch.jpg",
                "EXACT_SKU_IMAGE",
            ),
            _exact_product(
                "gold-1l-zepto",
                "Amul Gold Homogenised Standardised Milk",
                "amul-gold-full-cream",
                "Zepto",
                83,
                "1 L",
                "https://cdn.test/amul-gold-1l-tetra.jpg",
                "EXACT_SKU_IMAGE",
            ),
        ],
        related_results=[],
        rejected_results=[],
        provider_status={},
    )

    by_weight = {
        next(iter({offer["product"]["weightVolume"] for offer in group["offers"]})): group
        for group in groups
    }
    assert by_weight["500 ml"]["image_url"] == "https://cdn.test/amul-gold-500ml-pouch.jpg"
    assert by_weight["1 L"]["image_url"] == "https://cdn.test/amul-gold-1l-tetra.jpg"
    assert by_weight["500 ml"]["offers"][0]["image_url"] == "https://cdn.test/amul-gold-500ml-pouch.jpg"
    assert by_weight["1 L"]["offers"][0]["image_url"] == "https://cdn.test/amul-gold-1l-tetra.jpg"


def test_canonical_group_does_not_borrow_other_size_image_when_sku_image_missing() -> None:
    groups = build_canonical_offer_groups(
        query="Amul gold milk",
        category="Grocery",
        selected_identity={"entity_id": "selected-amul-gold-milk"},
        exact_results=[
            _exact_product(
                "gold-500ml-bb",
                "Amul Gold Full Cream Milk Pouch",
                "amul-gold-full-cream",
                "BigBasket",
                32,
                "500 ml",
                "",
                "NO_IMAGE",
            ),
            _exact_product(
                "gold-1l-zepto",
                "Amul Gold Homogenised Standardised Milk",
                "amul-gold-full-cream",
                "Zepto",
                83,
                "1 L",
                "https://cdn.test/amul-gold-1l-tetra.jpg",
                "EXACT_SKU_IMAGE",
            ),
        ],
        related_results=[],
        rejected_results=[],
        provider_status={},
    )

    by_weight = {
        next(iter({offer["product"]["weightVolume"] for offer in group["offers"]})): group
        for group in groups
    }
    assert by_weight["500 ml"]["image_url"] is None
    assert by_weight["500 ml"]["offers"][0]["image_url"] is None
    assert by_weight["500 ml"]["offers"][0]["image_match_status"] == "NO_IMAGE"


def test_canonical_group_keeps_single_litre_and_bulk_pack_images_separate() -> None:
    groups = build_canonical_offer_groups(
        query="Amul gold milk",
        category="Grocery",
        selected_identity={"entity_id": "selected-amul-gold-milk"},
        exact_results=[
            _exact_product(
                "gold-1l-zepto",
                "Amul Gold Homogenised Standardised Milk",
                "amul-gold-full-cream",
                "Zepto",
                83,
                "1 L",
                "https://cdn.test/amul-gold-1l-single.jpg",
                "EXACT_SKU_IMAGE",
            ),
            _exact_product(
                "gold-12x1l-swiggy",
                "Amul Gold Homogenised Standardised Milk",
                "amul-gold-full-cream",
                "Swiggy Instamart",
                996,
                "1 ltr x 12",
                "https://cdn.test/amul-gold-12x1l-case.jpg",
                "EXACT_SKU_IMAGE",
            ),
        ],
        related_results=[],
        rejected_results=[],
        provider_status={},
    )

    by_weight = {
        next(iter({offer["product"]["weightVolume"] for offer in group["offers"]})): group
        for group in groups
    }
    assert by_weight["1 L"]["image_url"] == "https://cdn.test/amul-gold-1l-single.jpg"
    assert by_weight["1 ltr x 12"]["image_url"] == "https://cdn.test/amul-gold-12x1l-case.jpg"
