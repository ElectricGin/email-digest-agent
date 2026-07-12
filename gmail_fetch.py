import argparse
import json

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build


def load_credentials(token_path):
    creds = Credentials.from_authorized_user_file(token_path)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open(token_path, "w", encoding="utf-8") as f:
            f.write(creds.to_json())
    return creds


def build_gmail_service(creds):
    return build("gmail", "v1", credentials=creds)


def fetch_messages_since(service, since_epoch_seconds):
    query = f"after:{since_epoch_seconds}"
    result = service.users().messages().list(
        userId="me", q=query, maxResults=50
    ).execute()
    message_ids = [m["id"] for m in result.get("messages", [])]

    messages = []
    for mid in message_ids:
        msg = service.users().messages().get(
            userId="me", id=mid, format="metadata",
            metadataHeaders=["From", "Subject", "Date"]
        ).execute()
        headers = {h["name"]: h["value"] for h in msg["payload"]["headers"]}
        messages.append({
            "id": mid,
            "from": headers.get("From", ""),
            "subject": headers.get("Subject", ""),
            "date": headers.get("Date", ""),
            "snippet": msg.get("snippet", ""),
        })
    return messages


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--token-path", required=True)
    parser.add_argument("--since-epoch", type=int, required=True)
    args = parser.parse_args()

    creds = load_credentials(args.token_path)
    service = build_gmail_service(creds)
    messages = fetch_messages_since(service, args.since_epoch)
    print(json.dumps(messages))


if __name__ == "__main__":
    main()
