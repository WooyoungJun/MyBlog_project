from flask import abort, flash, jsonify, redirect, render_template, url_for, request, current_app
from flask_login import login_required, current_user
from functools import wraps

# ------------------------------------------------- decorator 메소드 -------------------------------------------------
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.have_admin_check(): return abort(403)
        return f(*args, **kwargs)
    return decorated_function

def logout_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.is_authenticated:
            Msg.error_msg('로그아웃 한 뒤 시도해주세요.')
            return redirect(url_for('views.home'))
        return f(*args, **kwargs)
    return decorated_function

def login_and_create_permission_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.have_create_permission(): return abort(403)
        return f(*args, **kwargs)
    return decorated_function

def login_and_not_have_create_permission_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if current_user.have_create_permission(): 
            Msg.error_msg('이미 인증된 사용자입니다.')
            return redirect(url_for('views.home'))
        return f(*args, **kwargs)
    return decorated_function

def render_template_with_user(**context):
    context['user'] = current_user
    return render_template(**context)

# ------------------------------------------------- 소유자 확인, 메소드 체크, 폼 체크, 메세지, 에러 핸들러-------------------------------------------------
def is_owner(id):
    return id == current_user.id

from datetime import datetime, timedelta, timezone
def get_korea_time():
    # 한국 시간대 오프셋(UTC+9)을 생성합니다.
    KST_offset = timezone(timedelta(hours=9))
    return datetime.now(KST_offset)

def get_now_to_string():
    return str(int(datetime.now().timestamp()*100000))

def get_current_app():
    return current_app

def get_config():
    return current_app.config

def get_current_user():
    return current_user

def get_s3_config():
    config = get_config()
    return config['S3'], config['S3_BUCKET_NAME'], config['S3_DEFAULT_DIRS'][config['mode']]

from os.path import splitext
def make_new_file_name(filename, s3_default_dir):
    origin_file_name, extension = splitext(filename)
    origin_file_name = origin_file_name.replace(' ', '_')
    now = get_now_to_string()
    new_file_name = origin_file_name + '_' + now + extension
    if len(new_file_name) + len(s3_default_dir) > 150: 
        # 길이 제한 150자
        new_file_name = new_file_name[-150 + len(s3_default_dir)]
    return new_file_name

def generate_download_urls(files):
    if not files or not files[0]: return
    config = get_config()
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
    def delete_success(cls, msg):
        cls.success_msg(msg)
        return jsonify(message='success'), 200

    @classmethod
    def delete_error(cls, msg):
        cls.error_msg(msg)
        return jsonify(message='error'), 404

from flask import abort
def error(code):
    abort(code)