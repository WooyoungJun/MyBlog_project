import secrets
from flask import Blueprint, redirect, url_for, request
from flask_login import login_required, login_user, logout_user, current_user
from .utils import (
    logout_required, only_post_method,
    not_have_create_permission_required, render_template_with_user,     # 데코레이터 함수

    form_invalid, success_msg, error_msg, get_method,                   # 기타

    smtp_setup, smtp_send_mail,
    save_session, session_update, delete_session,
    get_otp, get_remain_time,                                           # email 인증

    make_auth_url, get_access_token, get_user_info                      # third-party 인증
)
from .forms import LoginForm, OtpForm, SignUpForm
from .models import get_model

auth = Blueprint('auth', __name__)
BASE_AUTH_DIR = 'auth/'

def render_template_auth(template_name_or_list, **context):
    context['template_name_or_list'] = template_name_or_list
    return render_template_with_user(BASE_AUTH_DIR, **context)

@auth.route('/mypage', methods=['GET', 'POST'])
@login_required
def mypage():
    session_update()
    form = OtpForm()
    session_otp = get_otp()
    remain_time = get_remain_time()
    params = {
        'otp':session_otp,
        'remain_time':remain_time,
        'form':form,
    }
    
    if get_method(): return render_template_auth("mypage.html", **params)

    if form_invalid(form):
        error_msg('otp 비밀번호는 6자리입니다. 길이를 맞춰주세요')
        return render_template_auth("mypage.html", **params)
    
    otp = form.otp.data
    if otp != session_otp:
        error_msg('otp 비밀번호가 일치하지 않습니다.')
        return render_template_auth("mypage.html", **params)
    
    delete_session()
    current_user.save_instance(create_permission=True)
    success_msg('이메일 인증 완료')
    return render_template_auth("mypage.html")

@auth.route('/send_mail_otp', methods=['POST'])
@only_post_method
@not_have_create_permission_required
def send_mail_otp():
    try:
        smtp = smtp_setup()
        otp = smtp_send_mail(smtp)
        success_msg('인증번호 전송 완료')
        save_session(otp)
    except Exception as e:
        error_msg(str(e))
    finally:
        smtp.quit()

    return redirect(url_for('auth.mypage'))

@auth.route('/login', methods=['GET', 'POST'])
@logout_required
def login():
    form = LoginForm()
    params = {
        'form': form,
        'type': 'login',
    }

    if get_method(): return render_template_auth('auth.html', **params)
    
    if form_invalid(form):
        error_msg('로그인 실패. 유효성 검사 실패')
        return render_template_auth('auth.html', **params)
    
    user, status = get_model('user').user_check(email=form.email.data, password=form.password.data)
    if not user:
        error_msg(f'{status}')
        return render_template_auth('auth.html', **params)
    
    login_user(user, remember=True)
    success_msg('로그인 성공!')
    return redirect(url_for('views.home'))

@auth.route('/logout')
@login_required
def logout():
    logout_user() 
    success_msg('로그아웃 성공!')
    return redirect(url_for('views.home'))

@auth.route('/sign-up', methods=['GET', 'POST'])
@logout_required
def sign_up():
    form = SignUpForm()
    params = {
        'form': form,
        'type': 'signup',
    }

    if get_method(): return render_template_auth('auth.html', **params)
    
    if form_invalid(form):
        error_msg('회원가입 실패. 유효성 검사 실패')
        return render_template_auth('auth.html', **params)

    if get_model('user').duplicate_check(email=form.email.data, username=form.username.data):
        error_msg('중복된 정보가 존재합니다')
        return render_template_auth('auth.html', **params)
    
    get_model('user')( 
        username = form.username.data,
        email = form.email.data,
        password = form.password.data,
    ).add_instance()
    success_msg('회원가입 완료!')
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
        error_msg(f'ACCESS_TOKEN 에러 코드: {access_token.status_code}\n{access_token}')
        return redirect(url_for('views.home'))
    
    response = get_user_info(domain='google', access_token=access_token.json()['access_token'])
    if response.status_code != 200:
        error_msg(f'userinfo RESPONSE 에러 코드: {response.status_code}\n{response}')
        return redirect(url_for('views.home'))

    if type == 'login':
        '''
            로그인
            1. 이메일 데이터 가져와서 db 체크
            2. login_user(user)
        '''
        user = get_model('user').get_instance(email=response.json()['email'])
        if not user:
            error_msg('회원 가입이 필요한 이메일입니다.')
            return redirect(url_for('views.home'))
        
        login_user(user, remember=True)
        success_msg('로그인 성공!')
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
            error_msg('중복된 정보가 존재합니다.')
            return redirect(url_for('views.home'))

        get_model('user')(
            username=user_data['name'],
            email=user_data['email'],
            password=secrets.token_hex(16),
            create_permission=True,
            is_third_party=True,
        ).add_instance()
        success_msg('회원가입 완료!')
        return redirect(url_for('views.home'))
        
