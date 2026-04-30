import os
import sys
from pathlib import Path

# Force the backend into local mode before importing app modules. This keeps
# tests fast and avoids touching DynamoDB or S3.
os.environ["LOCAL_DEV"] = "1"
os.environ["SECRET_KEY"] = "test-secret-at-least-32-characters"

# Add the generator package root to Python's import path so tests can import
# `src.*` modules when pytest runs from the repository root.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.app import create_app
from src.security import hash_password
from src.storage import LOCAL_UPLOAD_DIR, create_user, get_history


def make_client():
    """Create a Flask test client for calling routes without starting a server."""
    app = create_app()
    return app.test_client()


def register_and_login(client, username="user", password="password"):
    """Create a user and return a valid JWT for protected endpoint tests."""
    client.post("/users", json={"username": username, "password": password})
    login = client.post("/login", json={"username": username, "password": password})
    return login.get_json()["token"]


def test_register_and_login():
    client = make_client()

    # Register should create the account and return public user data.
    register = client.post(
        "/users",
        json={"username": "alice", "password": "password"},
    )
    assert register.status_code == 201
    assert register.get_json()["username"] == "alice"

    # Login should accept the same credentials and return a token the frontend
    # can use on authenticated requests.
    login = client.post(
        "/login",
        json={"username": "alice", "password": "password"},
    )
    assert login.status_code == 200
    assert login.get_json()["token"]


def test_register_requires_username_and_password():
    client = make_client()

    # Missing password is rejected before a user record can be created.
    response = client.post("/users", json={"username": "missing-password"})

    assert response.status_code == 400
    assert response.get_json()["error"] == "Username and password required!"


def test_register_rejects_duplicate_username():
    client = make_client()

    # The first request creates the username; the second one should hit the
    # duplicate-user guard in the register route.
    client.post("/users", json={"username": "duplicate", "password": "password"})
    response = client.post(
        "/users",
        json={"username": "duplicate", "password": "password"},
    )

    assert response.status_code == 409
    assert response.get_json()["error"] == "Username already exists!"


def test_login_rejects_wrong_password():
    client = make_client()

    # The user exists, but hashing the submitted password should not match the
    # stored hash, so the route returns a credentials error.
    client.post("/users", json={"username": "wrong-pass", "password": "password"})
    response = client.post(
        "/login",
        json={"username": "wrong-pass", "password": "bad-password"},
    )

    assert response.status_code == 401
    assert response.get_json()["error"] == "Invalid credentials!"


def test_protected_endpoint_requires_token():
    client = make_client()

    # /history is protected by token_required and should fail without a token.
    response = client.get("/history")

    assert response.status_code == 401
    assert response.get_json()["error"] == "Token is missing!"


def test_protected_endpoint_rejects_invalid_token():
    client = make_client()

    # A malformed Bearer token reaches the decorator but fails JWT decoding.
    response = client.get(
        "/history",
        headers={"Authorization": "Bearer invalid-token"},
    )

    assert response.status_code == 401
    assert response.get_json()["error"] == "Invalid token!"


def test_generate_qr_and_history():
    client = make_client()
    token = register_and_login(client, "bob")

    # Authenticated QR generation returns an embeddable base64 PNG by default.
    generate = client.post(
        "/generate",
        json={"content": "https://example.com", "upload": False},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert generate.status_code == 200
    assert generate.get_json()["qr"].startswith("data:image/png;base64,")

    # Saving happens during generation, so the same user's history should now
    # contain exactly one record.
    history = client.get("/history", headers={"Authorization": f"Bearer {token}"})
    assert history.status_code == 200
    assert len(history.get_json()["history"]) == 1


def test_generate_requires_content():
    client = make_client()
    token = register_and_login(client, "empty-content")

    # The route requires content because there is nothing meaningful to encode
    # into a QR code otherwise.
    response = client.post(
        "/generate",
        json={"upload": False},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == "Invalid input!"


def test_generate_qr_with_upload_returns_local_image_url():
    client = make_client()
    token = register_and_login(client, "carol")

    # LOCAL_DEV upload mode writes to local_uploads and returns a URL served by
    # the Flask app instead of an S3 object URL.
    generate = client.post(
        "/generate",
        json={"content": "https://example.com", "upload": True},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert generate.status_code == 200
    assert generate.get_json()["qr"].startswith(
        "http://127.0.0.1:5001/local_uploads/"
    )


def test_generate_qr_with_upload_writes_local_file():
    client = make_client()
    token = register_and_login(client, "file-upload")

    # This checks the side effect behind the returned local upload URL: a PNG
    # file should exist on disk under the configured local upload directory.
    response = client.post(
        "/generate",
        json={"content": "file content", "upload": True},
        headers={"Authorization": f"Bearer {token}"},
    )

    image_url = response.get_json()["qr"]
    local_path = Path(str(image_url).replace("http://127.0.0.1:5001/local_uploads/", ""))

    assert response.status_code == 200
    assert (LOCAL_UPLOAD_DIR / local_path).exists()


def test_history_is_only_for_current_user():
    client = make_client()
    first_token = register_and_login(client, "history-user-a")
    second_token = register_and_login(client, "history-user-b")

    # The first user creates history.
    client.post(
        "/generate",
        json={"content": "first user", "upload": False},
        headers={"Authorization": f"Bearer {first_token}"},
    )

    # The second user should not see the first user's QR record.
    second_history = client.get(
        "/history",
        headers={"Authorization": f"Bearer {second_token}"},
    )

    assert second_history.status_code == 200
    assert second_history.get_json()["history"] == []


def test_get_user_does_not_return_password_hash():
    client = make_client()
    token = register_and_login(client, "safe-user")

    # Login gives us the generated user id, which is needed for the lookup route.
    login_user = client.post(
        "/login",
        json={"username": "safe-user", "password": "password"},
    ).get_json()

    # The profile endpoint should return only safe public fields.
    response = client.get(
        f"/users/{login_user['userId']}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.get_json() == {
        "userId": login_user["userId"],
        "username": "safe-user",
    }


def test_missing_route_returns_json_404():
    client = make_client()

    # Unknown routes should still return JSON so API clients have a predictable
    # error shape.
    response = client.get("/does-not-exist")

    assert response.status_code == 404
    assert response.get_json()["error"] == "Not found!"


def test_hash_password_is_deterministic_and_not_plain_text():
    # Deterministic hashing allows login comparisons, while the output should
    # not reveal the original password.
    hashed = hash_password("password")

    assert hashed == hash_password("password")
    assert hashed != "password"
    assert len(hashed) == 64


def test_storage_keeps_history_sorted_newest_first():
    # This calls storage directly to verify the same newest-first behavior used
    # by the /history endpoint.
    user = create_user("storage-sort", hash_password("password"))

    from src.storage import save_history

    save_history(user["userId"], "2026-01-01T00:00:00+00:00", "old", "old-qr")
    save_history(user["userId"], "2026-01-02T00:00:00+00:00", "new", "new-qr")

    items = get_history(user["userId"])

    assert items[0]["content"] == "new"
    assert items[1]["content"] == "old"
