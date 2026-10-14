from fastapi.testclient import TestClient
from uuid import uuid4
from app.main import app


def test_login_returns_tokens_without_password():
    client = TestClient(app)
    email = f"guest-{uuid4().hex}@example.com"
    registration = client.post('/auth/register', json={'email': email, 'password': 'secret123!', 'name': '고객', 'phone': '01012345678'})
    assert registration.status_code == 201

    response = client.post('/auth/login', json={'email': email, 'password': 'secret123!'})

    assert response.status_code == 200
    assert {'access_token', 'refresh_token'} <= response.json().keys()
    assert 'secret123!' not in response.text
