import requests
import datetime
import json
import os
import time
from dotenv import load_dotenv
import logging
from datetime import datetime
load_dotenv()
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type, before_log, after_log
from requests.exceptions import ReadTimeout, HTTPError, RequestException

class RateLimitException(Exception):
    pass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Retry configuration using tenacity
@retry(
    stop=stop_after_attempt(10),
    wait=wait_exponential(multiplier=1, min=2, max=40),
    retry=retry_if_exception_type((RequestException, RateLimitException, ReadTimeout)),
    before=before_log(logger, logging.INFO),
    after=after_log(logger, logging.INFO),
)
def call_api(tenant, token, end_point):
    url = f"{os.getenv('BASE_URL')}{end_point}"
    headers = {
        'xero-tenant-id': tenant,
        'Authorization': f'Bearer {token}',
        'Accept': 'application/json',
        'Content-Type': 'application/json',
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except HTTPError as e:
        if response.status_code == 429:
            retry_after = int(response.headers.get('Retry-After', 10))
            logger.warning(f"Rate limit exceeded, retrying after {retry_after} seconds: {e}")
            raise RateLimitException(f"Rate limit exceeded: {e}")
        logger.error(f"HTTP error occurred: {e}")
        raise
    except ReadTimeout as e:
        logger.error(f"Read timeout error occurred: {e}")
        raise
    except RequestException as e:
        logger.error(f"Request error occurred: {e}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error occurred: {e}")
        return False
    
def parse_datetime(datetime_str):
    try:
        return datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S.%f")
    except ValueError:
        return datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S")
    
def format_date(date_string):
    try:
        if date_string:
            timestamp_start = date_string.find('(') + 1
            timestamp_end = date_string.find(')')
            if timestamp_start != -1 and timestamp_end != -1:
                timestamp_str = date_string[timestamp_start:timestamp_end]
                timestamp = int(timestamp_str.split('+')[0]) / 1000
                return datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
        return None
    except Exception as e:
        logging.error(f"Connection FormatDate: {e}")

