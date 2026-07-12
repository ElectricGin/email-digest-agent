import argparse
import os

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


def run_oauth_flow(client_secret_path, token_output_path):
    flow = InstalledAppFlow.from_client_secrets_file(client_secret_path, SCOPES)
    creds = flow.run_local_server(port=0, access_type="offline", prompt="consent")
    if not creds.refresh_token:
        raise RuntimeError(
            "No refresh token returned — the scheduled routine cannot run unattended "
            "without one. Revoke app access at https://myaccount.google.com/permissions "
            "and re-run this script."
        )
    os.makedirs(os.path.dirname(token_output_path), exist_ok=True)
    with open(token_output_path, "w", encoding="utf-8") as f:
        f.write(creds.to_json())
    print(f"Saved token to {token_output_path}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--client-secret", required=True)
    parser.add_argument("--account-label", required=True,
                         help="e.g. personal1, personal2, personal3 (must match accounts.json)")
    args = parser.parse_args()

    secrets_dir = os.path.join(
        os.path.expanduser("~"), ".claude", "secrets", "email-digest"
    )
    token_path = os.path.join(secrets_dir, f"{args.account_label}-token.json")
    run_oauth_flow(args.client_secret, token_path)


if __name__ == "__main__":
    main()
