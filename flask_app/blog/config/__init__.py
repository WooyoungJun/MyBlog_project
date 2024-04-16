import os

class Config():
    BASE_DIR = os.path.dirname(os.path.dirname(__file__))
    BASE_DB_NAME = "blog.db"

    SQLALCHEMY_DATABASE_URI = 'sqlite:///{}'.format(os.path.join(BASE_DIR, BASE_DB_NAME))
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = True

    FLASK_ADMIN_SWATCH = 'Darkly' # 테마 설정
    
    # 개발용
    from .development import DEVELOPMENT_SECRET_KEY
    SECRET_KEY = DEVELOPMENT_SECRET_KEY

    # # 운영용
    # from .production import PRODUCTION_SECRET_KEY
    # SECRET_KEY = PRODUCTION_SECRET_KEY