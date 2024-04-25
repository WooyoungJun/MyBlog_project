import requests
import secrets
from functools import wraps
from urllib.parse import urlencode
from flask import Blueprint, redirect, render_template, flash, url_for, current_app, request
from flask_login import login_required, login_user, logout_user, current_user
from .forms import LoginForm, SignUpForm
from .models import get_model

auth = Blueprint('auth', __name__)
BASE_AUTH_DIR = 'auth/'

def logout_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.is_authenticated:
            return redirect(url_for('views.home'))
        return f(*args, **kwargs)
    return decorated_function

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
    redirect_uri = current_app.config['GOOGLE_REDIRECT_URIS'][f'{type}_{current_app.config['mode']}']
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
        
