import base64
import datetime
from io import BytesIO

import qrcode
from flask import Blueprint, jsonify, request

from src.security import token_required
from src.storage import get_history, save_history, upload_qr_png

qr_routes = Blueprint("qr_routes", __name__)


@qr_routes.route("/generate", methods=["POST"])
@token_required
def generate_qr(current_user_id):
    """Create a QR code for the authenticated user and store it in history."""
    # The decorator has already verified the token and injected `current_user_id`,
    # so every generated QR code can be tied back to the logged-in user.
    data = request.get_json() or {}
    content = data.get("content")
    should_upload = data.get("upload") is True

    # A QR code needs actual content to encode. Missing or empty content is a
    # client input problem, so the API returns a 400 response.
    if not content:
        return jsonify(error="Invalid input!"), 400

    # The QR library writes PNG bytes. By default the API returns those bytes as
    # a data URL, which the frontend can display directly in an <img> tag.
    png_bytes = make_qr_png(content)
    qr_code = "data:image/png;base64," + base64.b64encode(png_bytes).decode()

    # In AWS mode, upload=True stores the PNG in S3 and returns a public URL.
    # In local mode, upload is ignored and the base64 image is returned.
    if should_upload:
        uploaded_url = upload_qr_png(current_user_id, png_bytes)
        if uploaded_url:
            qr_code = uploaded_url

    # ISO timestamps sort correctly as strings, which is useful for DynamoDB's
    # range key and for local newest-first history sorting.
    created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
    save_history(current_user_id, created_at, content, qr_code)

    return (
        jsonify(
            qr=qr_code,
            userId=current_user_id,
            content=content,
            createdAt=created_at,
        ),
        200,
    )


@qr_routes.route("/history", methods=["GET"])
@token_required
def history(current_user_id):
    """Return QR history only for the authenticated user."""
    # Storage is responsible for filtering by user id, so callers never receive
    # another user's generated QR records.
    return jsonify(history=get_history(current_user_id)), 200


def make_qr_png(content):
    """Render the provided text into PNG bytes for API responses or uploads."""
    # `version=1` starts with the smallest QR size, and `fit=True` lets the
    # library grow the QR code if the content needs more room.
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(content)
    qr.make(fit=True)

    # The generated image is written to an in-memory buffer instead of a temp
    # file so the route can either base64 encode it or upload it immediately.
    image = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()
