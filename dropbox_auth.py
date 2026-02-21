"""
One-time setup script to obtain a Dropbox long-lived refresh token.

Usage:
    python dropbox_auth.py

Steps:
    1. Run this script once.
    2. Open the URL it prints in your browser and authorize the app.
    3. Paste the authorization code back into the terminal.
    4. Copy the printed DROPBOX_REFRESH_TOKEN into your .env file.

After this you will never need to re-run this script unless you explicitly
revoke access from your Dropbox app settings.
"""

import dropbox


def main():
    app_key = input("Enter your Dropbox App Key: ").strip()
    app_secret = input("Enter your Dropbox App Secret: ").strip()

    auth_flow = dropbox.DropboxOAuth2FlowNoRedirect(
        app_key,
        app_secret,
        token_access_type="offline",  # "offline" = returns a refresh token
    )

    authorize_url = auth_flow.start()
    print("\n--- Dropbox Authorization ---")
    print(f"1. Open this URL in your browser:\n\n   {authorize_url}\n")
    print("2. Click 'Allow' to authorize the app.")
    print("3. Copy the authorization code shown and paste it below.\n")

    auth_code = input("Enter the authorization code here: ").strip()

    try:
        oauth_result = auth_flow.finish(auth_code)
    except Exception as e:
        print(f"\nERROR - Could not complete authorization: {e}")
        return

    print("\n--- SUCCESS ---")
    print("Add these lines to your .env file:\n")
    print(f'DROPBOX_APP_KEY="{app_key}"')
    print(f'DROPBOX_APP_SECRET="{app_secret}"')
    print(f'DROPBOX_REFRESH_TOKEN="{oauth_result.refresh_token}"')
    print("\nNote: Remove or comment out the old DROPBOX_TOKEN line.")


if __name__ == "__main__":
    main()
