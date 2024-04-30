import os

class TestConfig():
    BASE_DIR = os.path.dirname(os.path.dirname(__file__))
    BASE_DB_NAME = 'test.db'

    SQLALCHEMY_DATABASE_URI = 'sqlite:///{}'.format(os.path.join(BASE_DIR, BASE_DB_NAME))
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = False

    SECRET_KEYS = {
        'TEST_SECRET_KEY': 'test',
    }

    from .test_secret import MAIL_PASSWORD
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_USERNAME = 'otter4752@gmail.com'
    MAIL_PASSWORD = MAIL_PASSWORD
    MAIL_PORT = 587
    MAIL_LIMIT_TIME = 180