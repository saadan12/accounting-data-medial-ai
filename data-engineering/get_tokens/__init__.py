import logging

import azure.functions as func
from get_tokens.get_tokens.get_token_from_key_vaulet import get_secrets


def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    secret_list = get_secrets()
    print(secret_list)
    logging.info(secret_list)
    
    return func.HttpResponse(
        secret_list,
        mimetype="application/json",
        status_code=200
    )
