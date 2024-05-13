import os

class Config():
    '''
    sqlalchemy 관련 config
    '''
    BASE_DIR = os.path.dirname(os.path.dirname(__file__))
    BASE_DB_DIR = os.path.join(BASE_DIR, 'db')
    BASE_DB_NAME = "blog.db"

    SQLALCHEMY_DATABASE_URI = 'sqlite:///{}'.format(os.path.join(BASE_DB_DIR, BASE_DB_NAME))
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = True

    from .development import DEVELOPMENT_SECRET_KEY
    from .production import PRODUCTION_SECRET_KEY, MAIL_PASSWORD
    SECRET_KEYS = {
        'DEVELOPMENT_SECRET_KEY': DEVELOPMENT_SECRET_KEY,
        'PRODUCTION_SECRET_KEY': PRODUCTION_SECRET_KEY
    }

    '''
    flask-admin 관련 config
    '''
    FLASK_ADMIN_SWATCH = 'darkly' # 테마 설정
    
    '''
    smtp 관련 config
    '''
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_USERNAME = 'otter4752@gmail.com'
    MAIL_PASSWORD = MAIL_PASSWORD
    MAIL_PORT = 587
    MAIL_LIMIT_TIME = 180

    '''
    AWS 관련 config
    '''
    from boto3 import client
    from .production import AWS_ACCESS_KEY, AWS_SECRET_KEY
    S3_BUCKET_NAME = 'myblog-file-server'
    S3_DEFAULT_DIRS = {
        'DEVELOPMENT_DIR': 'DEVELOPMENT/',
        'PRODUCTION_DIR': 'PRODUCTION/'
    }
    S3_BUCKET_REGION = 'ap-northeast-2'
    S3 = client('s3', region_name = S3_BUCKET_REGION,
                aws_access_key_id=AWS_ACCESS_KEY,
                aws_secret_access_key=AWS_SECRET_KEY)
    S3_URL_EXPIRATION_SECONDS = 300
    
    '''
    third-party 관련 config
    '''    
    def __init__(self):
        from json import load
        self.DOMAINS = ['GOOGLE', 'KAKAO']

        for domain in self.DOMAINS:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            json_file_path = os.path.join(script_dir, f'{domain.lower()}_json.json')

            with open(json_file_path, 'r') as f:
                client_secret_file = load(f)['web']
                setattr(self, f'{domain}_CLIENT_SECRET_FILE', client_secret_file)
                
    