
import json
import boto3
import uuid
import os
from datetime import datetime, timezone

s3 = boto3.client("s3")
dynamodb = boto3.resource("dynamodb")

BUCKET = os.environ["BUCKET_NAME"]
TABLE = dynamodb.Table(os.environ["TABLE_NAME"])

def response(status, body):
    return {
        "statusCode": status,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps(body)
    }

def lambda_handler(event, context):
    try:
        body = json.loads(event.get("body") or "{}")

        filename = body.get("filename", "")
        content_type = body.get("content_type", "")

        allowed = [
            "image/jpeg",
            "image/png"
        ]

        if content_type not in allowed:
            return response(400, {
                "error": "Gunakan JPG atau PNG"
            })

        if not filename or len(filename) > 150:
            return response(400, {
                "error": "Nama file tidak valid"
            })

        document_id = str(uuid.uuid4())

        extension = (
            ".jpg" if content_type == "image/jpeg"
            else ".png"
        )

        key = f"uploads/{document_id}{extension}"

        upload_url = s3.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": BUCKET,
                "Key": key,
                "ContentType": content_type
            },
            ExpiresIn=300
        )

        TABLE.put_item(
            Item={
                "document_id": document_id,
                "filename": filename,
                "s3_key": key,
                "status": "UPLOADING",
                "created_at": datetime.now(
                    timezone.utc
                ).isoformat()
            }
        )

        return response(200, {
            "document_id": document_id,
            "upload_url": upload_url,
            "message": "URL upload berhasil dibuat"
        })

    except Exception as e:
        print("ERROR:", str(e))
        return response(500, {
            "error": "Gagal membuat URL upload"
        })
