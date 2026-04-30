from flask import Blueprint, jsonify, make_response, request, session

from src.security import create_token, hash_password, token_required
from src.storage import create_user, find_user_by_id, find_user_by_username

auth_routes = Blueprint("auth_routes", __name__)


@auth_routes.route("/users", methods=["POST"])
def register():
    """Create a new user account from a username and password."""
    # `get_json()` can return None for an empty or invalid JSON body, so the
    # fallback keeps the validation checks below simple.
    data = request.get_json() or {}
    username = data.get("username")
    password = data.get("password")

    # Both fields are required because the username identifies the user and the
    # password is immediately hashed before storage.
    if not username or not password:
        return jsonify(error="Username and password required!"), 400

    # Usernames are treated as unique login names. Checking before insert gives
    # the frontend a clear conflict error instead of silently overwriting data.
    if find_user_by_username(username):
        return jsonify(error="Username already exists!"), 409

    # Only the password hash is saved. The plain password never leaves this
    # function after the hash has been calculated.
    user = create_user(username, hash_password(password))
    return (
        jsonify(
            userId=user["userId"],
            username=user["username"],
            message="User created successfully",
        ),
        201,
    )


@auth_routes.route("/login", methods=["POST"])
def login():
    """Verify credentials and return a JWT for future authenticated requests."""
    data = request.get_json() or {}
    username = data.get("username")
    password = data.get("password")

    # Fail fast when the browser omits either field, before doing any storage
    # lookup or password hashing work.
    if not username or not password:
        return jsonify(error="Username and password required!"), 400

    # The stored value is a hash, so the submitted password is hashed and then
    # compared against the stored hash.
    user = find_user_by_username(username)
    if not user or user["password"] != hash_password(password):
        return jsonify(error="Invalid credentials!"), 401

    # The frontend stores this JWT and sends it in the Authorization header.
    token = create_token(user)
    session["token"] = token

    response = make_response(
        jsonify(
            userId=user["userId"],
            username=user["username"],
            token=token,
            message="Login successful",
        ),
        200,
    )
    # The response includes the token in JSON for the frontend state and as an
    # HTTP-only cookie for browser-managed requests.
    response.set_cookie(
        "token",
        value=token,
        max_age=86400,
        secure=True,
        httponly=True,
        samesite="Strict",
    )
    return response


@auth_routes.route("/users/<user_id>", methods=["GET"])
@token_required
def get_user(user_id, current_user_id):
    """Return public profile data for a user after token authentication."""
    # `token_required` verifies the caller first and passes the authenticated
    # user's id as `current_user_id`. This route only exposes safe profile data.
    user = find_user_by_id(user_id)
    if not user:
        return jsonify(error="User not found"), 404

    # Never return password hashes to the browser.
    return jsonify(userId=user["userId"], username=user["username"]), 200


@auth_routes.route("/logout", methods=["POST"])
@token_required
def logout(current_user_id):
    """Remove server-side and browser-side token state."""
    # Clearing the Flask session removes any token saved during login.
    session.clear()
    response = make_response(jsonify(message="Logged out successfully"), 200)

    # Deleting the cookie tells the browser to stop sending the old token.
    response.delete_cookie("token", secure=True, httponly=True, samesite="Strict")
    return response
