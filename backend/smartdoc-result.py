
import json
import boto3
import os
from decimal import Decimal

dynamodb = boto3.resource("dynamodb")

TABLE = dynamodb.Table(
    os.environ["TABLE_NAME"]
)

def convert_decimal(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

def lambda_handler(event, context):

    try:
        params = event.get("queryStringParameters") or {}
        document_id = params.get("id")

        if not document_id:
            return {
                "statusCode": 400,
                "body": json.dumps({
                    "error": "ID dokumen diperlukan"
                })
            }

        result = TABLE.get_item(
            Key={"document_id": document_id}
        )

        item = result.get("Item")

        if not item:
            return {
                "statusCode": 404,
                "body": json.dumps({
                    "error": "Dokumen tidak ditemukan"
                })
            }

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json"
            },
            "body": json.dumps(
                item,
                default=convert_decimal
            )
        }

    except Exception as e:
        print("ERROR:", str(e))

        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": "Gagal mengambil hasil OCR"
            })
        }
