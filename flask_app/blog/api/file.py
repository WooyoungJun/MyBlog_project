from flask import current_app
from datetime import datetime
from os.path import splitext
from flask_login import current_user

from .utils import Msg
from .models import get_model

def check_can_upload(files):
    total_size = sum(file.getbuffer().nbytes for file in files)
    return total_size <= current_user.get_limit()

def file_to_s3(file):
    config = current_app.config
    s3, s3_bucket_name = config['S3'], config['S3_BUCKET_NAME']
    s3_default_dir = config['S3_DEFAULT_DIRS'][config['mode'] + '_DIR']

    origin_file_name, extension = splitext(file.filename)
    origin_file_name = origin_file_name.replace(' ','_')
    now = str(int(datetime.now().timestamp()*100000))
    new_file_name = origin_file_name + '_' + now + extension
    if len(new_file_name) + len(s3_default_dir) > 150: 
        # 길이 제한 150자
        new_file_name = new_file_name[-150 + len(s3_default_dir)]

    s3.upload_fileobj(file, s3_bucket_name, s3_default_dir + new_file_name)
    return new_file_name

def upload_files(files, post_id):
    if not check_can_upload(files): 
        Msg.error_msg('일일 파일 업로드 할당량을 초과하였습니다.')
        files = None

    if not files or not files[0]: return

    upload_size = 0.0
    for file in files:
        try:
            file_size = file.getbuffer().nbytes
            new_file_name = file_to_s3(file)

            get_model('file')(
                name=new_file_name,
                size=file_size,
                post_id=post_id,
            ).add_instance()
            upload_size += file_size
            file.close()
        except Exception as e:
            Msg.error_msg(str(e) + f'{file.filename} upload 실패')

    if upload_size == 0.0: return
    current_user.update_limit(upload_size)

def generate_download_urls(files):
    if not files: return
    config = current_app.config
    s3, s3_bucket_name = config['S3'], config['S3_BUCKET_NAME']
    s3_default_dir = config['S3_DEFAULT_DIRS'][config['mode'] + '_DIR']

    download_urls = []
    for file in files:
        presigned_url = s3.generate_presigned_url(
            ClientMethod='get_object',
            Params={
                'Bucket': s3_bucket_name,
                'Key': s3_default_dir + file.name
            },
            ExpiresIn=3600,
        )
        download_urls.append(presigned_url)
    
    return download_urls
        