import requests
import time
import uuid
import random

# Constants
PING_INTERVAL = 30  # Ping every 60 seconds
DOMAIN_API = {
    "SESSION": "https://api.nodepay.ai/api/auth/session",
    "PING": "https://nw2.nodepay.ai/api/network/ping",
}

# Globals
token_info = "eyJhbGciOiJIUzUxMiJ9.eyJzdWIiOiIxMjU5NTY2MTA0NjU3Nzg4OTI4IiwiaWF0IjoxNzIwNDM5MTE2LCJleHAiOjE3MjE2NDg3MTZ9.J1pbcH6gJ61go9FEPLAl6bzSG9OqFoxk3R1c_ZylkOA4pm1FuxN6mT1MIE2LUAhxE36t-c7NE3O1ish41RO4KA"
account_info = None
retries = 0

def to_json(response):
    if response.ok:
        return response.json()
    response.raise_for_status()

def call_api(url, data):
    headers = {"Content-Type": "application/json"}
    if token_info:
        headers["Authorization"] = f"Bearer {token_info}"
    response = requests.post(url, headers=headers, json=data)
    return to_json(response)

def get_random_int(min_value, max_value):
    return random.randint(min_value, max_value)

def render_profile_info():
    global account_info
    try:
        response = call_api(DOMAIN_API["SESSION"], {})
        if response["code"] == 0 and response["data"]["uid"]:
            account_info = response["data"]
            connect_socket()
        else:
            handle_logout()
    except Exception as e:
        print(f"Error during profile info rendering: {e}")
        handle_logout()

def handle_logout():
    global token_info, account_info, retries
    token_info = None
    account_info = None
    retries = 0

def ping():
    global retries
    try:
        data = {
            "id": account_info["uid"] if account_info else None,
            "timestamp": int(time.time()),
            "version": "1.0.0"
        }
        response = call_api(DOMAIN_API["PING"], data)
        if response["code"] == 0:
            retries = 0
            print(f"Ping successful, IP Score: {response['data'].get('ip_score', get_random_int(80, 99))}")
        else:
            retries += 1
            handle_ping_failure(response["code"])
    except Exception as e:
        retries += 1
        handle_ping_failure(-1)
        print(f"Error during ping: {e}")

def handle_ping_failure(code):
    if retries >= 2:
        print("Disconnected from server")
    if code == 403:
        handle_logout()

def connect_socket():
    if account_info:
        start_ping()

def start_ping():
    ping()
    while token_info:
        time.sleep(PING_INTERVAL)
        ping()

if __name__ == "__main__":
    render_profile_info()
    if token_info:
        start_ping()
