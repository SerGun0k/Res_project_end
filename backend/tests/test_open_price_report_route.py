from app.main import app


def test_open_price_report_route_registered():
    paths = {route.path for route in app.routes}
    assert "/api/v1/import-open-prices-report/latest" in paths
