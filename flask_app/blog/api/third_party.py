from urllib.parse import urlencode
from flask import current_app, request
import requests

from .utils import error_msg

def set_domain_config(app):
    config = app.config
    '''
    domain = 대문자
    client_secret_file = json 파일 읽어옴

        oauth google client 환경 변수
        CLIENT_ID = OAuth 서버로 보낼 때 필요한 서비스 주체의 ID, 클라이언트 애플리케이션 식별하는데 사용
        CLIENT_SECRET = 서비스 주체 비밀번호, 서버와 안전하게 통신하는데 사용
        PROJECT_ID = 프로젝트 ID(식별자)

        AUTH_URI = 사용자 인증을 위한 URL, 서비스에서 해당 url로 이동시키기
        REDIRECT_URI = OAuth 인증 후 리디렉션될 URL, 클라이언트가 인증 완료하면 이 URL로 이동하여 인증 코드 또는 액세스 토큰 수신
        TOKEN_URI = authorization code를 교환하고 액세스 토큰을 얻을 수 있는 URL, GRANT 타입으로 액세스 토큰을 요청할 때 사용
        AUTH_PROVIDER_X509_CERT_URL = 인증서의 URL, 클라이언트가 인증서의 유효성을 검증할 때 사용 
        SCOPE = 사용자 email과 이름, 프로필 사진등의 기본 profile 등 사용자 정보에 대한 권한 부여
    
    '''
    for domain in ['GOOGLE']:
        client_secret_file = config.get(f'{domain}_CLIENT_SECRET_FILE')
        config[f'{domain}'] = True
        config[f'{domain}_CLIENT_ID'] = client_secret_file['client_id']
        config[f'{domain}_CLIENT_SECRET'] = client_secret_file['client_secret']
        config[f'{domain}_REDIRECT_URIS'] = client_secret_file['redirect_uris']
        
        config[f'{domain}_AUTH_URI'] = client_secret_file['auth_uri']
        config[f'{domain}_TOKEN_URI'] = client_secret_file['token_uri']
        
        config[f'{domain}_SCOPE'] = 'email profile'
        config[f'{domain}_USERINFO_URI'] = client_secret_file['userinfo_uri']

def make_auth_url_and_set(app):
    config = app.config
    from itertools import product
    domains = ['GOOGLE']
    types = ['LOGIN', 'SIGNUP']
    modes = [config['mode']]
    all_combinations = list(product(domains, types, modes))

    for domain, type, mode in all_combinations:
        query_string = urlencode(dict(
            redirect_uri=config[f'{domain}_REDIRECT_URIS'][f'{type}_{mode}'],
            client_id=config[f'{domain}_CLIENT_ID'],
            scope=config[f'{domain}_SCOPE'],
            response_type='code',
        ))
        config[f'{domain}_{type}_{mode}_AUTH_PAGE_URL'] = f"{config[f'{domain}_AUTH_URI']}?{query_string}"

def not_exist_domain(domain):
    if not current_app.config.get(f'{domain.upper()}'):
        error_msg(f'{domain.upper()} 지원하지 않는 도메인입니다.')
        return True

def get_auth_url(domain, type):
    config = current_app.config
    domain, type = domain.upper(), type.upper()
    return config[f'{domain}_{type}_{config["mode"]}_AUTH_PAGE_URL']

def get_access_token(domain, type):
    domain, type = domain.upper(), type.upper()
    config = current_app.config

    access_token = requests.post(current_app.config.get(f'{domain}_TOKEN_URI'), data=dict(
        code=request.args.get('code'),
        client_id=config[f'{domain}_CLIENT_ID'],
        client_secret=config[f'{domain}_CLIENT_SECRET'],
        redirect_uri=config[f'{domain}_REDIRECT_URIS'][f'{type}_{config["mode"]}'],
        grant_type='authorization_code',
    ))
    return access_token

def get_user_info(domain, access_token):
    domain = domain.upper()

    response = requests.get(current_app.config[f'{domain}_USERINFO_URI'], params=dict(
        access_token=access_token
    ))
    return response