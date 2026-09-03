from __future__ import annotations

from app.services.cache import MemoryPriceCache, _key


def test_current_cache_key_is_query_provider_category_only() -> None:
    assert _key("Amul Gold Milk", "Blinkit", "Grocery") == _key(" amul gold milk ", "blinkit", "grocery")


def test_price_cache_should_isolate_same_query_across_locations() -> None:
    cache = MemoryPriceCache()
    cache.set(
        "Saffola Muesli",
        "Blinkit",
        "Grocery",
        [{"city": "Surat", "price": 195}],
        location={"pincode": "395009", "latitude": 21.1959, "longitude": 72.7933},
    )
    cache.set(
        "Saffola Muesli",
        "Blinkit",
        "Grocery",
        [{"city": "Bengaluru", "price": 225}],
        location={"pincode": "560001", "latitude": 12.9716, "longitude": 77.5946},
    )

    surat = cache.get("Saffola Muesli", "Blinkit", "Grocery", location={"pincode": "395009"})
    bengaluru = cache.get("Saffola Muesli", "Blinkit", "Grocery", location={"pincode": "560001"})
    assert surat != bengaluru
    assert surat[0]["city"] == "Surat"
    assert bengaluru[0]["city"] == "Bengaluru"


def test_grocery_observation_repository_should_pass_location_to_cache() -> None:
    from app.repositories.grocery_observation_repository import GroceryObservationRepository

    repo = GroceryObservationRepository()
    repo.write_observations("Amul Gold", "blinkit", [{"price": 70}], location={"pincode": "395009"})
    assert repo.search_observations("Amul Gold", location={"pincode": "395009"})
