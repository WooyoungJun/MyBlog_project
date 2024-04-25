import smtplib
import requests
import secrets
import time
from random import randint
from email.mime.text import MIMEText
from urllib.parse import urlencode
from flask import Blueprint, abort, jsonify, redirect, render_template, flash, session, url_for, current_app, request
from flask_login import login_required, login_user, logout_user, current_user
from .utils import logout_required
from .forms import LoginForm, SignUpForm
from .models import get_model

auth = Blueprint('auth', __name__)
BASE_AUTH_DIR = 'auth/'

@auth.route('/get_mail_authorized', methods=['POST'])
def get_mail_authorized():
    if request.method == 'GET': return abort(403)

    try:
        email = request.form.get('email')
        smtp = smtplib.SMTP(current_app.config['MAIL_SERVER'], 587)
        smtp.starttls() # TLS 암호화 보안 연결 설정
        smtp.login(current_app.config['MAIL_USERNAME'], current_app.config['MAIL_PASSWORD'])

        otp = str(randint(100000, 999999))
        msg = MIMEText(f'MyBlog 회원가입 \n인증번호를 입력하여 이메일 인증을 완료해 주세요.\n인증번호 :{otp}')
        msg['Subject'] = '[MyBlog 이메일 인증]'
        smtp.sendmail(current_app.config['MAIL_USERNAME'], email, msg.as_string())
        flash('메세지 전송 완료', category="success")

        session[f'otp_{email}'] = otp  # 세션에 인증번호 저장
        session[f'time_{email}'] = int(time.time())  # 인증번호 생성 시간 저장
        smtp.quit()
        return redirect(url_for('auth.mail_check', email=email))
    except Exception as e:
        return jsonify({'status': 'fail', 'response':jsonify(e)})

@auth.route('/mail_check/<string:email>')
def mail_check(email):
    if f'otp_{email}' not in session: return abort(403)
    return render_template(BASE_AUTH_DIR + 'mail_check.html', user=current_user)

@auth.route('/login', methods=['GET', 'POST'])
@logout_required
def login():
    form = LoginForm()
    params = {
        'form': form,
        'user': current_user,
        'type': 'login',
    }

    if request.method == 'GET': return render_template(BASE_AUTH_DIR + 'auth.html', **params)
    
    if not form.validate_on_submit():
        flash('로그인 실패. 유효성 검사 실패', category="error")
        return render_template(BASE_AUTH_DIR + 'auth.html', **params)

    user, status = get_model('user').login_check(email=form.email.data, password=form.password.data)
    if user:
        login_user(user, remember=True)
        flash('로그인 성공!', category="success")
        return redirect(url_for('views.home'))
    
    flash(f'{status}', category="error")
    return render_template(BASE_AUTH_DIR + 'auth.html', **params)

@auth.route('/logout')
@login_required
def logout():
    logout_user() 
    flash('로그아웃 성공!', category="success")
    return redirect(url_for('views.home'))

@auth.route('/sign-up', methods=['GET', 'POST'])
@logout_required
def sign_up():
    form = SignUpForm()
    params = {
        'form': form,
        'user': current_user,
        'type': 'signup',
    }

    if request.method == 'GET': return render_template(BASE_AUTH_DIR + 'auth.html', **params)

    if not form.validate_on_submit():
        flash('회원가입 실패. 유효성 검사 실패', category="error")
        return render_template(BASE_AUTH_DIR + 'auth.html', **params)

    if get_model('user').duplicate_check(email=form.email.data, username=form.username.data):
        flash('중복된 정보가 존재합니다', category="error")
        return render_template(BASE_AUTH_DIR + 'auth.html', **params)
    
    get_model('user')( 
        username = form.username.data,
        email = form.email.data,
        password = form.password.data,
    ).add_instance()
    flash('회원가입 완료!', category="success")
    return redirect(url_for('views.home'))

@auth.route('/google/<string:type>')
def google_auth_page(type):
    authorize_uri = current_app.config['GOOGLE_AUTH_URI']
    redirect_uri = current_app.config['GOOGLE_REDIRECT_URIS'][f'{type}_{current_app.config["mode"]}']
    client_id = current_app.config['GOOGLE_CLIENT_ID']
    scope = current_app.config['GOOGLE_SCOPE']
    response_type = 'code'
    
    query_string = urlencode(dict(
        redirect_uri=redirect_uri,
        client_id=client_id,
        scope=scope,
        response_type=response_type
    ))
    return redirect(f'{authorize_uri}?{query_string}')

@auth.route('/callback/google/<string:type>')
def callback_google(type):
    code = request.args.get('code')
    token_uri = current_app.config.get('GOOGLE_TOKEN_URI')
    client_id = current_app.config.get('GOOGLE_CLIENT_ID')
    client_secret = current_app.config.get('GOOGLE_CLIENT_SECRET')
    redirect_uri = current_app.config.get('GOOGLE_REDIRECT_URIS')[f'{type}_{current_app.config["mode"]}']
    grant_type = 'authorization_code'

    access_token = requests.post(token_uri, data=dict(
        code=code,
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        grant_type=grant_type
    ))
    
    if access_token.status_code != 200:
        flash(f'ACCESS_TOKEN 에러 코드: {access_token.status_code}', category="error")
        return redirect(url_for('views.home'))
    
    userinfo_uri = current_app.config['GOOGLE_USERINFO_URI']
    response = requests.get(userinfo_uri, params=dict(
        access_token=access_token.json()['access_token']
    ))

    if response.status_code != 200:
        flash(f'userinfo RESPONSE 에러 코드: {response.status_code}', category="error")
        return redirect(url_for('views.home'))

    if type == 'login':
        '''
            로그인
            1. 이메일 데이터 가져와서 db 체크
            2. login_user(user)
        '''
        user = get_model('user').get_instance(email=response.json()['email'])
        if not user:
            flash('가입하지 않은 이메일입니다.', category="error")
            return redirect(url_for('views.home'))
        
        login_user(user, remember=True)
        flash('로그인 성공!', category="success")
        return redirect(url_for('views.home'))
    else:
        '''
            회원가입
            1. 이메일, 이름 데이터 가져오기 ('email', 'name')
            2. db 이메일 중복 체크
            3. is_third_party = True로 계정 생성. 비밀번호는 랜덤 문자열 넣기 
        '''
        user_data = response.json()
        user = get_model('user').duplicate_check(email=user_data['email'], username=user_data['name'])

        if user: 
            flash('중복된 정보가 존재합니다.', category="error")
            return redirect(url_for('views.home'))

        get_model('user')(
            username=user_data['name'],
            email=user_data['email'],
            password=secrets.token_hex(16),
            post_create_permission=True,
            is_third_party=True
        ).add_instance()
        flash('회원가입 완료!', category="success")
        return redirect(url_for('views.home'))
        
