def test_pages_accessibles(client):
    response = client.get("/")
    assert response.status_code == 200

def test_error_routes(client):
    assert client.get("/test-401").status_code == 401
    assert client.get("/test-403").status_code == 403
    assert client.get("/test-404").status_code == 404
    assert client.get("/test-429").status_code == 429
    assert client.get("/test-500").status_code == 500
    assert client.get("/test-503").status_code == 503