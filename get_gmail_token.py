"""
get_gmail_token.py
==================
Run this ONCE locally to get your Gmail OAuth2 refresh token.
The refresh token never expires (unless you revoke it).

Steps:
  1. Run:  python get_gmail_token.py
  2. It opens a browser — log in with manupnaik639@gmail.com
  3. Copy the 3 values it prints and add them to Render → Environment

Usage:
  python get_gmail_token.py
"""

import json
import os
import urllib.parse
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer

# ── Paste your Google Cloud OAuth2 credentials here ────────────────────────
# Get these from: console.cloud.google.com → APIs & Services → Credentials
# Create "OAuth 2.0 Client ID" → Desktop app
CLIENT_ID     = input("Paste your GMAIL_CLIENT_ID:     ").strip()
CLIENT_SECRET = input("Paste your GMAIL_CLIENT_SECRET: ").strip()
# ───────────────────────────────────────────────────────────────────────────

REDIRECT_URI  = "http://localhost:8765"
SCOPE         = "https://www.googleapis.com/auth/gmail.send"
AUTH_URL      = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL     = "https://oauth2.googleapis.com/token"

auth_code_holder = {}


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        auth_code_holder["code"] = params.get("code", [""])[0]
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(
            b"<h2>Done! You can close this tab and go back to the terminal.</h2>"
        )

    def log_message(self, *args):
        pass  # suppress HTTP logs


def main():
    # Step 1 — Open the authorization URL
    params = {
        "client_id":     CLIENT_ID,
        "redirect_uri":  REDIRECT_URI,
        "response_type": "code",
        "scope":         SCOPE,
        "access_type":   "offline",   # get refresh_token
        "prompt":        "consent",   # force refresh_token even if already granted
    }
    url = AUTH_URL + "?" + urllib.parse.urlencode(params)
    print("\nOpening browser for Google login...")
    print(f"If it doesn't open, visit:\n{url}\n")
    webbrowser.open(url)

    # Step 2 — Catch the redirect on localhost
    server = HTTPServer(("localhost", 8765), Handler)
    server.handle_request()   # handles exactly one request then stops
    code = auth_code_holder.get("code", "")
    if not code:
        print("ERROR: No auth code received.")
        return

    # Step 3 — Exchange code for tokens
    data = urllib.parse.urlencode({
        "code":          code,
        "client_id":     CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uri":  REDIRECT_URI,
        "grant_type":    "authorization_code",
    }).encode()

    req  = urllib.request.Request(TOKEN_URL, data=data, method="POST")
    with urllib.request.urlopen(req) as resp:
        tokens = json.loads(resp.read())

    refresh_token = tokens.get("refresh_token", "")
    if not refresh_token:
        print("ERROR: No refresh_token in response. Make sure prompt=consent was used.")
        print("Full response:", tokens)
        return

    # Step 4 — Print what to add to Render
    print("\n" + "=" * 60)
    print("SUCCESS! Add these to Render → Environment Variables:")
    print("=" * 60)
    print(f"GMAIL_CLIENT_ID     = {CLIENT_ID}")
    print(f"GMAIL_CLIENT_SECRET = {CLIENT_SECRET}")
    print(f"GMAIL_REFRESH_TOKEN = {refresh_token}")
    print(f"SENDER_EMAIL        = manupnaik639@gmail.com")
    print(f"SENDER_NAME         = Zero Click AI")
    print(f"EMAIL_PROVIDER      = gmail")
    print("=" * 60)
    print("\nYou do NOT need SMTP_* or RESEND_API_KEY once these are set.")


if __name__ == "__main__":
    main()
