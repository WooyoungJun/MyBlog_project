import smtplib
import time
from urllib.parse import urlencode
from flask import abort, flash, redirect, url_for, session, request, current_app
from flask_login import login_required, current_user
from email.mime.text import MIMEText
from functools import wraps
from random import randint

import requests

def logout_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.is_authenticated:
            flash('로그아웃 한 뒤 시도해주세요.', category='error')
            return redirect(url_for('views.home'))
        return f(*args, **kwargs)
    return decorated_function

def only_post_method(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.method == 'GET': abort(403)
        return f(*args, **kwargs)
    return decorated_function

def create_permission_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.create_permission: 
            flash('이메일 인증이 필요합니다.', category='error')
            return redirect(url_for('views.home'))
        return f(*args, **kwargs)
    return decorated_function

def not_have_create_permission_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if current_user.create_permission: 
            flash('이미 인증된 사용자입니다.', category='error')
            return redirect(url_for('views.home'))
        return f(*args, **kwargs)
    return decorated_function

def is_owner(id):
    return id == current_user.id

def instance_check(instance, msg):
    if instance is None:
        flash(f'해당 {msg} 객체는 존재하지 않습니다.', category="error")
        return redirect(url_for('views.home'))

def smtp_setup():
    smtp = smtplib.SMTP(host=current_app.config['MAIL_SERVER'], port=current_app.config['MAIL_PORT'])
    smtp.starttls() # TLS 암호화 보안 연결 설정
    smtp.login(current_app.config['MAIL_USERNAME'], current_app.config['MAIL_PASSWORD'])
    return smtp

def smtp_send_mail(smtp):
    otp = str(randint(100000, 999999))
    msg = MIMEText(f'MyBlog 회원가입 \n인증번호를 입력하여 이메일 인증을 완료해 주세요.\n인증번호 :{otp}')
    msg['Subject'] = '[MyBlog 이메일 인증]'
    smtp.sendmail(current_app.config['MAIL_USERNAME'], current_user.email, msg.as_string())
    return otp

def save_session(otp):
    session[f'otp_{current_user.email}'] = otp  # 세션에 인증번호 저장
    session[f'time_{current_user.email}'] = int(time.time()) + current_app.config['MAIL_LIMIT_TIME']  # 인증번호 제한 시간

def delete_session():
    session.pop(f'otp_{current_user.email}')
    session.pop(f'time_{current_user.email}')

def get_otp():
    return session.get(f'otp_{current_user.email}')

def get_time():
    return session.get(f'time_{current_user.email}')

def get_remain_time():
    session_time = get_time()
    if not session_time: return None
    return session_time - int(time.time())

def session_update():
    session_otp = get_otp()
    if not session_otp: return None

    if get_remain_time() < 0: delete_session()

def make_auth_url(domain, type):
    domain = domain.upper()
    
    query_string = urlencode(dict(
        redirect_uri=current_app.config[f'{domain}_REDIRECT_URIS'][f'{type}_{current_app.config["mode"]}'],
        client_id=current_app.config[f'{domain}_CLIENT_ID'],
        scope=current_app.config[f'{domain}_SCOPE'],
        response_type='code'
    ))
    return f"{current_app.config[f'{domain}_AUTH_URI']}?{query_string}"

def get_access_token(domain, type):
    domain = domain.upper()

    access_token = requests.post(current_app.config.get(f'{domain}_TOKEN_URI'), data=dict(
        code=request.args.get('code'),
        client_id=current_app.config.get(f'{domain}_CLIENT_ID'),
        client_secret=current_app.config.get(f'{domain}_CLIENT_SECRET'),
        redirect_uri=current_app.config.get(f'{domain}_REDIRECT_URIS')[f'{type}_{current_app.config["mode"]}'],
        grant_type='authorization_code'
    ))
    return access_token