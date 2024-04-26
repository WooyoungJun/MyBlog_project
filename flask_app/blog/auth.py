import requests
import secrets
from flask import Blueprint, redirect, render_template, flash, url_for, current_app, request
from flask_login import login_required, login_user, logout_user, current_user
from .utils import delete_session, get_access_token, get_otp, get_remain_time, instance_check, logout_required, make_auth_url, not_have_create_permission_required, only_post_method, save_session, session_update, smtp_send_mail, smtp_setup
from .forms import LoginForm, OtpForm, SignUpForm
from .models import get_model

auth = Blueprint('auth', __name__)
BASE_AUTH_DIR = 'auth/'

@auth.route('/mypage', methods=['GET', 'POST'])
@login_required
def mypage():
    session_update()
    form = OtpForm()
    session_otp = get_otp()
    remain_time = get_remain_time()
    params = {
        'user':current_user,
        'otp':session_otp,
        'remain_time':remain_time,
        'form':form,
    }
    
    if request.method == 'GET': return render_template(BASE_AUTH_DIR + "mypage.html", **params)

    if not form.validate_on_submit():
        flash('otp 비밀번호는 6자리입니다. 길이를 맞춰주세요', category="error")
        return redirect(url_for('auth.mypage'))
    
    otp = form.otp.data
    if otp != session_otp:
        flash('otp 비밀번호가 일치하지 않습니다.', category="error")
        current_app.logger.debug(otp, session_otp)
        return redirect(url_for('auth.mypage'))
    
    delete_session()
    current_user.save_instance(create_permission=True)
    flash('이메일 인증 완료', category="success")
    return render_template(BASE_AUTH_DIR + "mypage.html", user=current_user)

@auth.route('/send_mail_otp', methods=['POST'])
@only_post_method
@not_have_create_permission_required
def send_mail_otp():
    try:
        smtp = smtp_setup()
        
        otp = smtp_send_mail(smtp)
        flash('인증번호 전송 완료', category="success")
        save_session(otp)
    except Exception as e:
        flash(str(e), category="error")
    finally:
        smtp.quit()

    return redirect(url_for('auth.mypage'))

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
    if not user:
        flash(f'{status}', category="error")
        return render_template(BASE_AUTH_DIR + 'auth.html', **params)
    
    login_user(user, remember=True)
    flash('로그인 성공!', category="success")
    return redirect(url_for('views.home'))


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
@logout_required
def google_auth_page(type):
    return redirect(make_auth_url(domain='google', type=type))

@auth.route('/callback/google/<string:type>')
@logout_required
def callback_google(type):
    access_token = get_access_token(domain='google', type=type)
    if access_token.status_code != 200:
        flash(f'ACCESS_TOKEN 에러 코드: {access_token.status_code}\n{access_token}', category="error")
        return redirect(url_for('views.home'))
    
    response = requests.get(current_app.config['GOOGLE_USERINFO_URI'], params=dict(
        access_token=access_token.json()['access_token']
    ))
    if response.status_code != 200:
        flash(f'userinfo RESPONSE 에러 코드: {response.status_code}\n{response}', category="error")
        return redirect(url_for('views.home'))

    if type == 'login':
        '''
            로그인
            1. 이메일 데이터 가져와서 db 체크
            2. login_user(user)
        '''
        user = get_model('user').get_instance(email=response.json()['email'])

        if instance_check(user, 'user'): return redirect(url_for('views.home'))
        
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
            create_permission=True,
            is_third_party=True
        ).add_instance()
        flash('회원가입 완료!', category="success")
        return redirect(url_for('views.home'))
        
