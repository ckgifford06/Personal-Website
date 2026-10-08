import json
import os
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler

METERS_PER_MILE = 1609.344


def get_access_token():
    data = urllib.parse.urlencode({
        "client_id": os.environ["STRAVA_CLIENT_ID"],
        "client_secret": os.environ["STRAVA_CLIENT_SECRET"],
        "refresh_token": os.environ["STRAVA_REFRESH_TOKEN"],
        "grant_type": "refresh_token",
    }).encode()
    req = urllib.request.Request("https://www.strava.com/oauth/token", data=data, method="POST")
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.load(resp)["access_token"]


def get_ytd_miles():
    token = get_access_token()
    athlete_id = os.environ["STRAVA_ATHLETE_ID"]
    req = urllib.request.Request(
        f"https://www.strava.com/api/v3/athletes/{athlete_id}/stats",
        headers={"Authorization": f"Bearer {token}"},
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        stats = json.load(resp)
    return round(stats["ytd_run_totals"]["distance"] / METERS_PER_MILE)


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            body = json.dumps({"ytd_miles": get_ytd_miles()})
            status = 200
            cache = "public, s-maxage=3600, stale-while-revalidate=86400"
        except Exception:
            body = json.dumps({"error": "unavailable"})
            status = 502
            cache = "no-store"
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", cache)
        self.end_headers()
        self.wfile.write(body.encode())
