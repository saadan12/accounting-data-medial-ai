import logging
import json
import requests
import os
from dotenv import load_dotenv
load_dotenv()
from azure.identity import ClientSecretCredential
from azure.keyvault.secrets import SecretClient

def get_access_token(refresh_token, accesstoken):
    print("I am in functions")
    url = f"https://identity.xero.com/connect/token?={accesstoken}"

    payload = {'grant_type': 'refresh_token',
    'refresh_token': refresh_token,
    'client_id': os.getenv('XERO_CLIENT_ID'),
    'client_secret': os.getenv('XERO_CLIENT_SECRET')}
    files=[
    
    ]
    headers = {
    'grant_type': 'refresh_token',
    'Content-Type': 'application/json'
    }
    response = requests.request("POST", url, data=payload)
    if response.status_code == 200:
        access_token = response.json().get('access_token')
        refresh_token = response.json().get('refresh_token')
        token_json = json.dumps({
            'access_token': access_token,
            'refresh_token': refresh_token
        })
        print("Refresh token in gen ", token_json)
        return token_json
    else:
        print(f"Failed to get access token: {response.text}")
        return accesstoken
    


def get_secrets():
    try:
        credential = ClientSecretCredential(
        
            tenant_id=os.getenv('TENANT_ID'),
            client_id=os.getenv('CLIENT_ID'),
            client_secret=os.getenv('CLIENT_SECRET')
        )
        vault_url = os.getenv('VAULT_URL')

        secret_client = SecretClient(vault_url=vault_url, credential=credential)

        secrets = secret_client.list_properties_of_secrets()

        secret_list = []
        for secret in secrets:
            secret_name = secret.name
            secret_value = secret_client.get_secret(secret_name).value
            print(secret_value)
            if isinstance(secret_value, str):
                try:
                    secret_value = json.loads(secret_value)
                except json.JSONDecodeError as e:
                    logging.error(f"Failed to parse secret value: {e}")
                    continue  # Skip to the next secret

            # Access tokens
            token_json = get_access_token(secret_value['refresh_token'], secret_value['access_token'])
            secret_client.set_secret(secret_name, token_json)
            secret_dict = {
                "secret_name": secret_name,
                "secret_value": token_json  # storing the new token JSON
            }
            secret_list.append(secret_dict)

        return json.dumps(secret_list)
    except Exception as e:
        logging.info("failure due to " + str(e))