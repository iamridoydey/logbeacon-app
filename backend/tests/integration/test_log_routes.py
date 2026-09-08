def test_get_logs_requires_login(client):
    response = client.get("/log")
    assert response.status_code == 401


def test_create_and_get_log_authenticated(client):
    with client:
        client.post("/auth/register", json={
            "username": "ridoy", "email": "ridoy@email.com", "password": "secret123"
        })
        client.post("/auth/signin", json={
            "username": "ridoy", "password": "secret123"
        })

        create_response = client.post("/log", json={
            "error_log": "NullPointerException at line 42",
            "error_solution": "Add a null check before dereferencing"
        })
        assert create_response.status_code == 201

        get_response = client.get("/log")
        assert get_response.status_code == 200

        body = get_response.get_json()
        assert "entries" in body
        assert "summary" in body