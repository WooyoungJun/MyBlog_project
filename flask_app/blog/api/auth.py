from secrets import token_hex
from flask import Blueprint, jsonify, redirect, url_for
from flask_login import login_required, login_user, logout_user, current_user

from .utils import (
    admin_required, logout_required, only_delete_method,
    not_have_create_permission_required, render_template_with_user,                 # 데코레이터 함수

    form_valid, form_invalid, success_msg, error_msg, get_method, post_method,      # 기타
)
from .email import (
    send_mail, session_update, delete_session, get_otp, get_remain_time,            # email 인증
)
from .third_party import (
    get_auth_url, get_access_token, get_user_info, not_exist_domain                 # third-party 인증
)
from .forms import CategoryForm, LoginForm, OtpForm, SignUpForm
from .models import get_model

auth = Blueprint('auth', __name__)
BASE_AUTH_DIR = 'auth/'

def render_template_auth(template_name_or_list, **context):
    context['template_name_or_list'] = BASE_AUTH_DIR + template_name_or_list
    return render_template_with_user(**context)

# ------------------------------------------------ 로그인, 로그아웃, 회원가입, 회원탈퇴 ------------------------------------------------
@auth.route('/login', methods=['GET', 'POST'])
@logout_required
def login():
    form = LoginForm()
    params = {
        'form': form,
        'type': 'login',
    }

    if get_method(): return render_template_auth('auth.html', **params)
    if form_invalid(form): return render_template_auth('auth.html', **params)
    
    user = get_model('user').user_check(email=form.email.data, password=form.password.data)
    if not user: return render_template_auth('auth.html', **params)
    
    login_user(user, remember=True)
    success_msg('로그인 성공!')
    return redirect(url_for('views.home'))

@auth.route('/logout')
@login_required
def logout():
    logout_user() 
    success_msg('로그아웃 성공!')
    return redirect(url_for('views.home'))

@auth.route('/signup', methods=['GET', 'POST'])
@logout_required
def signup():
    form = SignUpForm()
    params = {
        'form': form,
        'type': 'signup',
    }

    if get_method(): return render_template_auth('auth.html', **params)
    if form_invalid(form): return render_template_auth('auth.html', **params)
    if get_model('user').duplicate_check(email=form.email.data, username=form.username.data):
        return render_template_auth('auth.html', **params)
    
    get_model('user')( 
        username = form.username.data,
        email = form.email.data,
        password = form.password.data,
    ).add_instance()
    success_msg('회원가입 완료!')
    return redirect(url_for('views.home'))

@auth.route('/user-delete', methods=['DELETE'])
@only_delete_method
@login_required
def user_delete():
    user = get_model('user').get_instance_by_id(current_user.id)
    if not user: return jsonify(message='error'), 404
    logout_user()
    
    user.delete_instance()
    success_msg('성공적으로 탈퇴하였습니다.')
    return jsonify(message='success'), 200

# ------------------------------------------------ mypage, 이메일 인증 ------------------------------------------------
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
    if form_invalid(form): return render_template_auth("mypage.html", **params)

    if form.otp.data != session_otp:
        error_msg('otp 비밀번호가 일치하지 않습니다.')
        return render_template_auth("mypage.html", **params)
    
    delete_session()
    current_user.save_instance(create_permission=True)
    success_msg('이메일 인증 완료')
    return render_template_auth("mypage.html")

@auth.route('/send-mail-otp')
@not_have_create_permission_required
def send_mail_otp():
    try:
        send_mail()
        success_msg('인증번호 전송 완료')
    except Exception as e:
        error_msg(str(e))
    return redirect(url_for('auth.mypage'))

@auth.route("/make-category", methods=['GET', 'POST'])
@admin_required
def make_category():
    form = CategoryForm()

    if post_method() and form_valid(form):
        if not get_model('category').duplicate_check(name=form.name.data):
            get_model('category')(name=form.name.data).add_instance()
            success_msg(f'{form.name.data} category 생성에 성공하였습니다.')
        form.name.data = ''

    return render_template_auth("make_category.html", form=form)

# ------------------------------------------------ third-party 가입 ------------------------------------------------
@auth.route('/<string:domain>/<string:type>')
@logout_required
def google_auth_page(domain, type):
    if not_exist_domain(domain): return redirect(url_for(f'auth.{type}'))
    return redirect(get_auth_url(domain=domain, type=type))

@auth.route('/callback/<string:domain>/<string:type>')
@logout_required
def callback_google(domain, type):
    access_token = get_access_token(domain=domain, type=type)
    if access_token.status_code != 200:
        error_msg(f'ACCESS_TOKEN 에러 코드: {access_token.status_code}\n{access_token}')
        return redirect(url_for('views.home'))
    
    response = get_user_info(domain=domain, access_token=access_token.json()['access_token'])
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
        if not user: return redirect(url_for('auth.login'))
        
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
        if get_model('user').duplicate_check(email=user_data['email'], username=user_data['name']): 
            return redirect(url_for('auth.signup'))

        get_model('user')(
            username=user_data['name'],
            email=user_data['email'],
            password=token_hex(16),
            create_permission=True,
            is_third_party=True,
        ).add_instance()
        success_msg('회원가입 완료!')
        return redirect(url_for('views.home'))
        