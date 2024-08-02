import requests
import time
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from requests.packages.urllib3.exceptions import InsecureRequestWarning

# Suppress only the single InsecureRequestWarning from urllib3 needed
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# Constants
PING_INTERVAL = 30  # Ping every 30 seconds
DOMAIN_API = {
    "SESSION": "https://api.nodepay.ai/api/auth/session",
    "PING": "https://nw2.nodepay.ai/api/network/ping",
}
MAX_WORKERS = 1000  # Number of concurrent workers

# Globals
token_info = "NP_TOKEN"
account_info = None

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# List of proxies
proxies = [
]

def to_json(response):
    if response.ok:
        return response.json()
    response.raise_for_status()

def call_api(url, data, proxy, timeout=60):
    headers = {"Content-Type": "application/json"}
    if token_info:
        headers["Authorization"] = f"Bearer {token_info}"
    proxy_url = f"{proxy['protocol'].lower()}://{proxy['ip']}:{proxy['port']}"
    proxy_dict = {"http": proxy_url, "https": proxy_url}
    logging.info(f"Using proxy: {proxy_url}")
    try:
        response = requests.post(url, headers=headers, json=data, proxies=proxy_dict, verify=False, timeout=timeout)
        return to_json(response)
    except Exception as e:
        logging.error(f"Request error with proxy {proxy_url}: {e}")
        return None

def render_profile_info():
    global account_info
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(call_api, DOMAIN_API["SESSION"], {}, proxy): proxy for proxy in proxies}
        for future in as_completed(futures):
            proxy = futures[future]
            try:
                account_info = future.result()
                if account_info:
                    logging.info(f"Profile info retrieved successfully with proxy {proxy['ip']}: {account_info}")
                    return True
            except Exception as e:
                logging.error(f"Error retrieving profile info with proxy {proxy['ip']}: {e}")
    logging.error("Failed to retrieve profile info")
    return False

def send_ping(proxy):
    while True:
        response = call_api(DOMAIN_API["PING"], {}, proxy)
        if response:
            logging.info(f"Ping response from {proxy['ip']}: {response}")
        else:
            logging.error(f"Failed to ping server using {proxy['ip']}")
        time.sleep(PING_INTERVAL)

def main():
    logging.info("Starting script...")
    if render_profile_info():
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = {executor.submit(send_ping, proxy): proxy for proxy in proxies}
            for future in as_completed(futures):
                proxy = futures[future]
                try:
                    result = future.result()
                    if result is not None:
                        logging.info(f"Future result: {result}")
                except Exception as e:
                    logging.error(f"Error in pinging with proxy {proxy['ip']}: {e}")
    else:
        logging.error("Unable to start pinging due to profile info retrieval failure")

if __name__ == "__main__":
    main()
