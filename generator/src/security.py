import datetime
import hashlib
from functools import wraps

import jwt
from flask import current_app, jsonify, make_response, request, session


def hash_password(password):
    """Hash a password before comparing or storing it."""
    # The app stores hashes, not plain text passwords. This deterministic hash
    # lets login compare the submitted password with the saved value.
    return hashlib.sha256(password.encode()).hexdigest()


def create_token(user):
    """Create a signed JWT that identifies a logged-in user for 24 hours."""
    # The token payload contains only the fields needed by protected routes.
    # `exp` is understood by PyJWT and automatically rejects old tokens.
    token = jwt.encode(
        payload={
            "user_id": user["userId"],
            "username": user["username"],
            "exp": datetime.datetime.now(datetime.timezone.utc)
            + datetime.timedelta(hours=24),
        },
        key=current_app.config["SECRET_KEY"],
        algorithm="HS256",
    )

    # Some PyJWT versions return bytes and newer versions return str. Returning
    # a str keeps the rest of the app independent of that version difference.
    if isinstance(token, bytes):
        return token.decode("utf-8")
    return token


def token_required(route_handler):
    """Wrap a Flask route so it only runs when a valid token is present."""
    @wraps(route_handler)
    def decorated(*args, **kwargs):
        # Tokens may come from the Authorization header, Flask session, or
        # cookie. `_read_token` keeps that lookup order in one place.
        token = _read_token()
        if not token:
            return make_response(jsonify(error="Token is missing!"), 401)

        try:
            # Decoding verifies the signature and expiration using the app's
            # SECRET_KEY. Invalid or expired tokens raise PyJWT exceptions.
            decoded_token = jwt.decode(
                token, current_app.config["SECRET_KEY"], algorithms=["HS256"]
            )
            # Protected route handlers receive the authenticated user's id as a
            # named argument, so they do not need to decode the JWT themselves.
            return route_handler(
                *args, current_user_id=decoded_token["user_id"], **kwargs
            )
        except jwt.ExpiredSignatureError:
            # Expired tokens are removed from session/cookie state so the
            # browser can prompt the user to log in again cleanly.
            session.pop("token", None)
            response = make_response(jsonify(error="Token has expired!"), 401)
            response.delete_cookie("token")
            return response
        except jwt.InvalidTokenError:
            # Covers malformed tokens, bad signatures, and other JWT failures.
            return make_response(jsonify(error="Invalid token!"), 401)

    return decorated


def _read_token():
    """Read the auth token from the supported request locations."""
    # API clients and the React frontend normally send `Authorization: Bearer`.
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header.split(" ", 1)[1]

    # Flask session support exists because login saves the token server-side.
    if "token" in session:
        return session["token"]

    # The HTTP-only cookie is a browser fallback for requests that include
    # credentials but do not manually set an Authorization header.
    return request.cookies.get("token")
