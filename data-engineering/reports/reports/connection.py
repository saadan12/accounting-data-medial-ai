import json
import requests
import jwt
from datetime import datetime
import re
import logging


def extract_user_id(string):
    try:
        # Use regular expression to find all sequences of digits in the string
        match = re.findall(r'\d+', string)
        if match:
            # Convert the first match to an integer
            return int(match[0])
        else:
            return None
    except Exception as e:
        logging.error(f"Connection Extract UserId: {e}")

def get_tenant_id(token):
    try:
        url = "https://api.xero.com/connections"
        headers = {
            'Authorization': f'Bearer {token}',
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }
        try:
            # Fetch data from Xero API
            response = requests.get(url, headers=headers)
            data = json.loads(response.text)
            # Check if the response contains data
            if data and isinstance(data, list) and 'tenantId' in data[0]:
                return data[0]['tenantId']
            else:
                logging.info(f"Connection: No tenantId found in the response.")
                return None
        except Exception as e:
            logging.error(f"Connection GetTenantId: {e}")
            return None
    except Exception as e:
        logging.error(f"Connection GetTenantId: {e}")


def get_xero_user(token):
    try:
        jwt_token = (f"{token}")
        # Decoding the JWT token (assuming we have no secret or public key required for decoding)
        decoded_token = jwt.decode(jwt_token, options={"verify_signature": False})
        xero_userid = decoded_token.get('xero_userid')
        if xero_userid:
            return xero_userid
        else:
            return None
    except Exception as e:
        logging.error(f"Connection GetXeroUser: {e}")

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