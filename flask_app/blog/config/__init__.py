import os

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
    MAIL_LIMIT_TIME = 180

    def __init__(self):
        from json import load
        self.DOMAINS = ['GOOGLE', 'KAKAO']

        for domain in self.DOMAINS:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            json_file_path = os.path.join(script_dir, f'{domain.lower()}_json.json')

            with open(json_file_path, 'r') as f:
                client_secret_file = load(f)['web']
                setattr(self, f'{domain}_CLIENT_SECRET_FILE', client_secret_file)
                
    