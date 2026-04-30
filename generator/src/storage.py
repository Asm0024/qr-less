import os
import uuid
from pathlib import Path

import boto3
from boto3.dynamodb.conditions import Key


# LOCAL_DEV=1 makes the backend run without AWS.
# It is only for local testing; deployed Lambda always uses DynamoDB and S3.
LOCAL_DEV = os.environ.get("LOCAL_DEV") == "1"
LOCAL_UPLOAD_BASE_URL = os.environ.get(
    "LOCAL_UPLOAD_BASE_URL", "http://127.0.0.1:5001/local_uploads"
)
LOCAL_UPLOAD_DIR = Path(__file__).resolve().parents[1] / "local_uploads"

# Local development uses process memory so the backend can run without AWS.
# These values reset every time the Flask process restarts.
users = {}
history = []

if not LOCAL_DEV:
    # In deployed mode the same helper functions below talk to AWS resources
    # created by serverless.yml.
    dynamodb = boto3.resource("dynamodb")
    users_table = dynamodb.Table(os.environ["USERS_TABLE"])
    history_table = dynamodb.Table(os.environ["HISTORY_TABLE"])
    s3 = boto3.client("s3")
    qr_bucket_name = os.environ["QR_BUCKET_NAME"]


def find_user_by_username(username):
    """Find a user by login name in local memory or DynamoDB."""
    if LOCAL_DEV:
        return users.get(username)

    # DynamoDB's primary key is userId, so username lookup uses the
    # UsernameIndex configured in serverless.yml.
    response = users_table.query(
        IndexName="UsernameIndex",
        KeyConditionExpression=Key("username").eq(username),
    )
    items = response.get("Items", [])
    return items[0] if items else None


def find_user_by_id(user_id):
    """Find a user by generated user id."""
    if LOCAL_DEV:
        # Local users are keyed by username, so finding by id requires scanning
        # the small in-memory dictionary.
        for user in users.values():
            if user["userId"] == user_id:
                return user
        return None

    # In DynamoDB, userId is the table's partition key, so this is a direct read.
    response = users_table.get_item(Key={"userId": user_id})
    return response.get("Item")


def create_user(username, password_hash):
    """Create and persist a user record."""
    # UUIDs avoid exposing usernames as database keys and give every account a
    # stable id for history records and uploaded QR paths.
    user = {
        "userId": str(uuid.uuid4()),
        "username": username,
        "password": password_hash,
    }

    if LOCAL_DEV:
        # Local storage is keyed by username because login starts from username.
        users[username] = user
    else:
        users_table.put_item(Item=user)

    return user


def save_history(user_id, created_at, content, qr_code):
    """Save one generated QR record for a user."""
    # The history item stores both the original content and the QR result. The
    # result may be a base64 data URL or an uploaded S3/local file URL.
    item = {
        "userId": user_id,
        "createdAt": created_at,
        "content": content,
        "qrCode": qr_code,
    }

    if LOCAL_DEV:
        # Appending locally mirrors DynamoDB writes while keeping setup simple.
        history.append(item)
    else:
        history_table.put_item(Item=item)

    return item


def get_history(user_id):
    """Return a user's QR history newest first."""
    if LOCAL_DEV:
        # Local mode filters in memory, then sorts by ISO timestamp descending.
        items = [item for item in history if item["userId"] == user_id]
        return sorted(items, key=lambda item: item["createdAt"], reverse=True)

    # DynamoDB uses userId as the partition key and createdAt as the sort key.
    # ScanIndexForward=False returns newest records first without app-side sort.
    response = history_table.query(
        KeyConditionExpression=Key("userId").eq(user_id),
        ScanIndexForward=False,
        Limit=50,
    )
    return response.get("Items", [])


def upload_qr_png(user_id, png_bytes):
    """Store QR PNG bytes and return a URL the frontend can display."""
    # Prefixing by user id keeps uploaded files grouped by owner.
    file_name = f"{user_id}/{uuid.uuid4()}.png"

    if LOCAL_DEV:
        # Local uploads are written to disk so the upload path can be tested
        # without S3. The Flask app serves these files from /local_uploads.
        file_path = LOCAL_UPLOAD_DIR / file_name
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_bytes(png_bytes)
        return f"{LOCAL_UPLOAD_BASE_URL}/{file_name}"

    # In AWS mode the PNG is written to the QR bucket and returned as a public
    # object URL because serverless.yml attaches a read policy to this bucket.
    s3.put_object(
        Bucket=qr_bucket_name,
        Key=file_name,
        Body=png_bytes,
        ContentType="image/png",
    )
    return f"https://{qr_bucket_name}.s3.amazonaws.com/{file_name}"
