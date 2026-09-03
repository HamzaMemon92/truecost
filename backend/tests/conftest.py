import os
import pytest

def pytest_configure(config):
    config.addinivalue_line(
        "markers", "live_provider: mark test as requiring live provider credentials"
    )

def pytest_runtest_setup(item):
    if "live_provider" in item.keywords:
        if os.environ.get("TRUECOST_LIVE_PROVIDER_TESTS", "").lower() != "true":
            pytest.skip("Skipping live provider tests (set TRUECOST_LIVE_PROVIDER_TESTS=true to run)")
