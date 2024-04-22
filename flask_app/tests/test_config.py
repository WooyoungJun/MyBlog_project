import os

class TestConfig():
    BASE_DIR = os.path.dirname(os.path.dirname(__file__))
    BASE_DB_NAME = 'test.db'

    SQLALCHEMY_DATABASE_URI = 'sqlite:///{}'.format(os.path.join(BASE_DIR, BASE_DB_NAME))
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = False

    SECRET_KEY = 'test'