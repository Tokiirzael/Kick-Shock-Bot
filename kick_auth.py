import base64
import hashlib
import os
import requests
import secrets

def generate_pkce_challenge():
    """
    Generates a PKCE code verifier and challenge.
    """
    code_verifier = secrets.token_urlsafe(64)
    code_challenge = hashlib.sha256(code_verifier.encode('utf-8')).digest()
    code_challenge = base64.urlsafe_b64encode(code_challenge).rstrip(b'=').decode('utf-8')
    return code_verifier, code_challenge

def get_access_token(client_id, client_secret, redirect_uri, code, code_verifier):
    """
    Exchanges an authorization code for an access token.
    """
    token_url = 'https://id.kick.com/oauth/token'
    data = {
        'grant_type': 'authorization_code',
        'code': code,
        'client_id': client_id,
        'client_secret': client_secret,
        'redirect_uri': redirect_uri,
        'code_verifier': code_verifier
    }
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    response = requests.post(token_url, data=data, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error getting access token: {response.text}")
        return None

def main():
    """
    Main function to guide the user through the authentication process.
    """
    print("Kick OAuth 2.1 Token Generator")
    print("--------------------------------")

    client_id = input("Enter your Client ID: ")
    client_secret = input("Enter your Client Secret: ")
    redirect_uri = input("Enter your Redirect URI: ")

    code_verifier, code_challenge = generate_pkce_challenge()

    # Corrected scopes based on the official documentation
    scopes = [
        "channel:read",
        "chat:write",
        "events:subscribe"
    ]
    scope_string = "+".join(scopes)

    auth_url = (
        f"https://id.kick.com/oauth/authorize?"
        f"response_type=code&"
        f"client_id={client_id}&"
        f"redirect_uri={redirect_uri}&"
        f"scope={scope_string}&"
        f"code_challenge={code_challenge}&"
        f"code_challenge_method=S256&"
        f"state=random_state"
    )

    print("\n1. Open the following URL in your browser. It should now ask for the correct permissions, including subscribing to events.")
    print(auth_url)

    code = input("\n2. After authorizing, paste the 'code' from the redirect URL here: ")

    tokens = get_access_token(client_id, client_secret, redirect_uri, code, code_verifier)

    if tokens:
        print("\nAuthentication successful!")
        print("Access Token:", tokens['access_token'])
        print("Refresh Token:", tokens['refresh_token'])
        print("\nCopy the new Access Token and paste it into your kick_bot.py configuration.")

if __name__ == '__main__':
    main()
