def test_register_success(client):
    response = client.post("/auth/register", json={
        "username": "ridoy",
        "email": "ridoy@email.com",
        "password": "secret123"
    })

    assert response.status_code == 201
    assert "api_key" in response.get_json()


def test_register_missing_fields(client):
    response = client.post("/auth/register", json={
        "username": "ridoy"
    })

    assert response.status_code == 400


def test_register_duplicate_username(client):
    client.post("/auth/register", json={
        "username": "ridoy", "email": "a@email.com", "password": "pass123"
    })
    response = client.post("/auth/register", json={
        "username": "ridoy", "email": "b@email.com", "password": "pass456"
    })

    assert response.status_code == 409


def test_signin_and_signout_flow(client):
    client.post("/auth/register", json={
        "username": "ridoy", "email": "ridoy@email.com", "password": "secret123"
    })

    signin_response = client.post("/auth/signin", json={
        "username": "ridoy", "password": "secret123"
    })
    assert signin_response.status_code == 200

    signout_response = client.post("/auth/signout")
    assert signout_response.status_code == 200