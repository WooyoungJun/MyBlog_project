import os

class TestConfig():
    '''
    sqlalchemy 관련 config
    '''
    BASE_DIR = os.path.dirname(__file__)
    BASE_DB_NAME = 'test.db'

    SQLALCHEMY_DATABASE_URI = 'sqlite:///{}'.format(os.path.join(BASE_DIR, BASE_DB_NAME))
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = False

    SECRET_KEYS = {
        'TEST_SECRET_KEY': 'test',
    }

    '''
    smtp 관련 config
    '''
    from .test_secret import MAIL_PASSWORD
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_USERNAME = 'otter4752@gmail.com'
    MAIL_PASSWORD = MAIL_PASSWORD
    MAIL_PORT = 587
    MAIL_LIMIT_TIME = 180

    '''
    AWS 관련 config
    '''
    from boto3 import client
    from .test_secret import AWS_ACCESS_KEY, AWS_SECRET_KEY
    S3_BUCKET_NAME = 'myblog-file-server'
    S3_DEFAULT_DIRS = {
        'TEST': 'TEST/'
    }
    S3_BUCKET_REGION = 'ap-northeast-2'
    S3 = client('s3', region_name = S3_BUCKET_REGION,
                aws_access_key_id=AWS_ACCESS_KEY,
                aws_secret_access_key=AWS_SECRET_KEY)
    S3_URL_EXPIRATION_SECONDS = 300