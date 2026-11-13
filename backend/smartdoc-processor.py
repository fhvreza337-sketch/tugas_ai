
import boto3
import json
import os
from urllib.parse import unquote_plus

textract = boto3.client("textract")
dynamodb = boto3.resource("dynamodb")

TABLE = dynamodb.Table(
    os.environ["TABLE_NAME"]
)

def lambda_handler(event, context):

    for record in event["Records"]:

        bucket = record["s3"]["bucket"]["name"]

        key = unquote_plus(
            record["s3"]["object"]["key"]
        )

        filename = key.split("/")[-1]
        document_id = filename.rsplit(".", 1)[0]

        try:
            # Update status
            TABLE.update_item(
                Key={"document_id": document_id},
                UpdateExpression="SET #s = :s",
                ExpressionAttributeNames={
                    "#s": "status"
                },
                ExpressionAttributeValues={
                    ":s": "PROCESSING"
                }
            )

            # Jalankan AI OCR
            result = textract.detect_document_text(
                Document={
                    "S3Object": {
                        "Bucket": bucket,
                        "Name": key
                    }
                }
            )

            # Ambil teks per baris
            lines = []

            for block in result["Blocks"]:
                if block["BlockType"] == "LINE":
                    lines.append(block["Text"])

            extracted_text = "\n".join(lines)

            # Simpan hasil ke DynamoDB
            TABLE.update_item(
                Key={"document_id": document_id},
                UpdateExpression=(
                    "SET #s = :s, "
                    "extracted_text = :t, "
                    "textract_version = :v"
                ),
                ExpressionAttributeNames={
                    "#s": "status"
                },
                ExpressionAttributeValues={
                    ":s": "COMPLETED",
                    ":t": extracted_text,
                    ":v": result.get(
                        "DetectDocumentTextModelVersion",
                        "unknown"
                    )
                }
            )

            print("OCR SUCCESS:", document_id)
            print(extracted_text)

        except Exception as e:

            print("OCR ERROR:", str(e))

            TABLE.update_item(
                Key={"document_id": document_id},
                UpdateExpression="SET #s = :s, error_message = :e",
                ExpressionAttributeNames={
                    "#s": "status"
                },
                ExpressionAttributeValues={
                    ":s": "FAILED",
                    ":e": str(e)[:1000]
                }
            )

    return {
        "statusCode": 200,
        "body": json.dumps("OCR processing finished")
    }
