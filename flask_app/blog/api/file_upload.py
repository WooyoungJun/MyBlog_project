from flask import current_app
from datetime import datetime
from os.path import splitext
from werkzeug.utils import secure_filename

def file_to_s3(file):
    config = current_app.config
    origin_file_name, extension = splitext(file.filename)
    origin_file_name = origin_file_name.replace(' ','_')
    now = str(int(datetime.now().timestamp()))
    file_name = origin_file_name + '_' + now + extension

    s3, s3_bucket_name = config['S3'], config['S3_BUCKET_NAME']
    s3_default_dir = config['S3_DEFAULT_DIRS'][config['mode'] + '_DIR']
    s3.upload_fileobj(file, s3_bucket_name, s3_default_dir + file_name)
    return file.filename
