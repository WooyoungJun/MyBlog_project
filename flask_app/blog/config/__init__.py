import os
import json

class Config():
    BASE_DIR = os.path.dirname(os.path.dirname(__file__))
    BASE_DB_DIR = os.path.join(BASE_DIR, 'db')
    BASE_DB_NAME = "blog.db"

    SQLALCHEMY_DATABASE_URI = 'sqlite:///{}'.format(os.path.join(BASE_DB_DIR, BASE_DB_NAME))
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = True

    FLASK_ADMIN_SWATCH = 'darkly' # 테마 설정
    
    from .development import DEVELOPMENT_SECRET_KEY
    from .production import PRODUCTION_SECRET_KEY, MAIL_PASSWORD
    SECRET_KEYS = {
        'DEVELOPMENT_SECRET_KEY': DEVELOPMENT_SECRET_KEY,
        'PRODUCTION_SECRET_KEY': PRODUCTION_SECRET_KEY
    }
    
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_USERNAME = 'otter4752@gmail.com'
    MAIL_PASSWORD = MAIL_PASSWORD
    MAIL_PORT = 587

    '''
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
    def __init__(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        json_file_path = os.path.join(script_dir, 'google_json.json')

        with open(json_file_path, 'r') as f:
            client_secret_file = json.load(f)['web']
        
        # GOOGLE 환경 변수 설정
        self.GOOGLE_CLIENT_ID = client_secret_file['client_id']
        self.GOOGLE_CLIENT_SECRET = client_secret_file['client_secret']
        self.GOOGLE_PROJECT_ID = client_secret_file['project_id']

        self.GOOGLE_AUTH_URI = client_secret_file['auth_uri']
        self.GOOGLE_REDIRECT_URIS = client_secret_file['redirect_uris']
        self.GOOGLE_TOKEN_URI = client_secret_file['token_uri']
        self.GOOGLE_AUTH_PROVIDER_X509_CERT_URL = client_secret_file['auth_provider_x509_cert_url']
        self.GOOGLE_SCOPE = 'email profile'
        self.GOOGLE_USERINFO_URI = 'https://www.googleapis.com/oauth2/v1/userinfo'