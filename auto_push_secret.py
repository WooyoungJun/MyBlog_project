from boto3 import client
from flask_app.blog.config.production import AWS_ACCESS_KEY, AWS_SECRET_KEY
S3_BUCKET_NAME = 'myblog-file-server'
S3_BUCKET_REGION = 'ap-northeast-2'
S3 = client('s3', region_name = S3_BUCKET_REGION,
            aws_access_key_id=AWS_ACCESS_KEY,
            aws_secret_access_key=AWS_SECRET_KEY)
S3_URL_EXPIRATION_SECONDS = 300

from os.path import dirname, abspath, join
script_dir = dirname(abspath(__file__))

relative_config = join('flask_app', 'blog', 'config')
relative_tests = join('flask_app', 'tests')

file_names = [
    join(relative_config, 'production.py'), 
    join(relative_config, 'google_json.json'), 
    join(relative_config, 'kakao_json.json'), 
    join(relative_tests, 'test_secret.py'),
]
for file_name in file_names:
    S3.upload_file(join(script_dir, file_name), S3_BUCKET_NAME, 'Config/' + file_name)
    print(f'upload {file_name} success')
