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

response = S3.list_objects_v2(Bucket=S3_BUCKET_NAME, Prefix='Config/')

if 'Contents' in response:
    for obj in response['Contents']:
        # flask_app/~ 이하 경로 
        file_name = obj['Key'].split('/')[-1]
        
        # S3에서 파일 다운로드
        download_path = join(script_dir, file_name).replace('\\', '/')
        S3.download_file(S3_BUCKET_NAME, obj['Key'], download_path)
        
        print(f'Downloaded {file_name} from S3 bucket to {download_path}')
else:
    print('No files found in the Config folder of S3 bucket.')