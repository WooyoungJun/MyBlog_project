from flask import flash, jsonify, request
from flask_login import current_user

class HttpMethod():
    @staticmethod
    def get():
        return request.method == 'GET'
    
    @staticmethod
    def post():
        return request.method == 'POST'
    
    @staticmethod
    def delete():
        return request.method == 'DELETE'
    
class Msg:
    @staticmethod
    def success_msg(msg):
        flash(msg, category="success")

    @staticmethod
    def error_msg(msg):
        flash(msg, category="error")

    @classmethod
    def delete_success(cls, msg=''):
        if msg: cls.success_msg(msg)
        return jsonify(message='success'), 200

    @classmethod
    def delete_error(cls, msg='', code=404):
        if msg: cls.error_msg(msg)
        return jsonify(message='error'), code

from datetime import datetime, timedelta, timezone
from os.path import splitext
class Etc():
    @classmethod
    def init_app(cls, app):
        cls.app = app
        cls.config = app.config
        cls.KST_offset = timezone(timedelta(hours=9))
    
    @classmethod
    def get_korea_time(cls):
        return datetime.now(cls.KST_offset)

    @classmethod
    def get_config(cls):
        return cls.config
    
    @classmethod
    def make_new_file_name(cls, filename, s3_default_dir):
        origin_file_name, extension = splitext(filename)
        origin_file_name = origin_file_name.replace(' ', '_')
        now = str(int(datetime.now().timestamp()*100000))
        new_file_name = origin_file_name + '_' + now + extension
        if len(new_file_name) + len(s3_default_dir) > 150: 
            # 길이 제한 150자
            new_file_name = new_file_name[-150 + len(s3_default_dir)]
        return new_file_name

    @classmethod
    def generate_download_urls(cls, files):
        if not files or not files[0]: return
        config = cls.config
        s3, s3_bucket_name = config['S3'], config['S3_BUCKET_NAME']
        s3_default_dir = config['S3_DEFAULT_DIRS'][config['mode']]

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
    
    @staticmethod
    def is_owner(id):
        return id == current_user.id