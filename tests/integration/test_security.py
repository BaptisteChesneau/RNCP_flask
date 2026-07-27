def test_sql_injection_login(client):
    malicious_input = "' OR 1=1; --"
    response = client.post(
        "/login",
        data={"email": malicious_input, "password": "fakepassword"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"invalide" in response.data.lower() or b"connexion" in response.data.lower()

def test_admin_route_protection(client):
    # Doit rediriger vers le login si non connecté
    response = client.get("/admin-chatbot")
    assert response.status_code == 302

    # Doit fonctionner une fois le flag admin en session
    with client.session_transaction() as sess:
        sess["admin_logged_in"] = True
    response = client.get("/admin-chatbot")
    assert response.status_code == 200