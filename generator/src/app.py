import os

from flask import Flask, jsonify, request, send_from_directory

from src.middleware import ApiPrefixMiddleware
from src.routes.auth_routes import auth_routes
from src.routes.qr_routes import qr_routes


def create_app():
    """Build and configure the Flask application.

    Keeping this setup in a function lets tests create a fresh app client while
    Serverless can still import the module-level `app` below for AWS Lambda.
    """
    app = Flask(__name__)

    # Load environment variables that use Flask's expected prefix format.
    # This makes deployed configuration available through `app.config`.
    app.config.from_prefixed_env()

    # SECRET_KEY signs login tokens. AWS deploy requires a real secret.
    # Local mode uses this simple default so the app starts quickly.
    app.config["SECRET_KEY"] = os.environ.get(
        "SECRET_KEY", "local-dev-secret-at-least-32-chars"
    )
    app.config["SESSION_COOKIE_SECURE"] = True
    app.config["SESSION_COOKIE_HTTPONLY"] = True

    # Blueprints keep route groups small: auth routes handle users and tokens,
    # while QR routes handle generation and history.
    app.register_blueprint(auth_routes)
    app.register_blueprint(qr_routes)

    # CloudFront sends API traffic as /api/*. Flask routes are written without
    # /api, so this removes the prefix before Flask matches the route.
    app.wsgi_app = ApiPrefixMiddleware(app.wsgi_app, "/api")

    @app.after_request
    def add_cors_headers(response):
        # The Vite dev server and CloudFront site can call the API from
        # different origins, so each response includes browser CORS headers.
        origin = request.headers.get("Origin") or "*"
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Headers"] = (
            "Content-Type,Authorization"
        )
        response.headers["Access-Control-Allow-Methods"] = (
            "GET,POST,PUT,PATCH,DELETE,OPTIONS"
        )
        return response

    @app.errorhandler(404)
    def resource_not_found(_error):
        # Return JSON for unknown API routes so frontend callers can handle the
        # error consistently instead of receiving Flask's default HTML page.
        return jsonify(error="Not found!"), 404

    @app.route("/local_uploads/<path:file_name>")
    def local_uploads(file_name):
        # In LOCAL_DEV mode uploaded QR PNGs are written to generator/local_uploads.
        # This route serves those files back to the frontend during development.
        return send_from_directory("../local_uploads", file_name)

    return app


# Serverless WSGI imports this value as `src.app.app` during deployment.
app = create_app()
