from app import app

client = app.test_client()


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.get_json() == {"status": "ok"}


def test_version():
    r = client.get("/version")
    assert r.status_code == 200
    assert r.get_json() == {"version": "1.0.0"}


def test_env(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "test")
    r = client.get("/env")
    assert r.get_json() == {"environment": "test"}


def test_config_lifecycle():
    item = {"name": "database_url", "value": "postgres://example"}

    assert client.post("/config", json=item).get_json() == item
    assert client.get("/config/database_url").get_json() == item
    assert client.delete("/config/database_url").get_json() == {"deleted": True}
    assert client.get("/config/database_url").status_code == 404


def test_config_missing_field():
    r = client.post("/config", json={"name": "only_name"})
    assert r.status_code == 400
