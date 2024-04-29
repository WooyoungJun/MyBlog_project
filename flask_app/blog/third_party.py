from urllib.parse import urlencode
from flask import current_app, request
import requests

def make_auth_url(domain, type):
    domain = domain.upper()

    query_string = urlencode(dict(
        redirect_uri=current_app.config[f'{domain}_REDIRECT_URIS'][f'{type}_{current_app.config["mode"]}'],
        client_id=current_app.config[f'{domain}_CLIENT_ID'],
        scope=current_app.config[f'{domain}_SCOPE'],
        response_type='code'
    ))
    return f"{current_app.config[f'{domain}_AUTH_URI']}?{query_string}"

def get_access_token(domain, type):
    domain = domain.upper()

    access_token = requests.post(current_app.config.get(f'{domain}_TOKEN_URI'), data=dict(
        code=request.args.get('code'),
        client_id=current_app.config.get(f'{domain}_CLIENT_ID'),
        client_secret=current_app.config.get(f'{domain}_CLIENT_SECRET'),
        redirect_uri=current_app.config.get(f'{domain}_REDIRECT_URIS')[f'{type}_{current_app.config["mode"]}'],
        grant_type='authorization_code'
    ))
    return access_token

def get_user_info(domain, access_token):
    domain = domain.upper()

    response = requests.get(current_app.config.get(f'{domain}_USERINFO_URI'), params=dict(
        access_token=access_token
    ))
    return response