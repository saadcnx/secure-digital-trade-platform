import pytest

from privacy_governance.region_store import (
    RegionRoutingError,
    route_country,
)


def test_germany_routes_to_demo_eu_region():
    assert route_country("DE") == "EU_SIMULATED"


def test_us_routes_to_demo_us_region():
    assert route_country("US") == "US_SIMULATED"


def test_pakistan_routes_to_demo_apac_region():
    assert route_country("PK") == "APAC_SIMULATED"


def test_unknown_country_is_not_silently_routed():
    with pytest.raises(RegionRoutingError):
        route_country("ZZ")
