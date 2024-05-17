from secrets import token_hex
from flask import Blueprint, redirect, url_for
from flask_login import login_required, login_user, logout_user, current_user

from .utils.decorator import Deco
from .utils.email import Email      
from .utils.third_party import ThirdParty                                      
from .utils.etc import Msg, HttpMethod
from .forms import LoginForm, OtpForm, SignUpForm, UserInfoForm
from .models import get_model

auth = Blueprint('auth', __name__)
BASE_AUTH_DIR = 'auth/'

def render_template_auth(template_name_or_list, **context):
    context['template_name_or_list'] = BASE_AUTH_DIR + template_name_or_list
    return Deco.render_template_with_user(**context)

# ------------------------------------------------ 로그인, 로그아웃, 회원가입, 회원탈퇴 ------------------------------------------------
@auth.route('/login', methods=['GET', 'POST'])
@Deco.logout_required
def login():
    form = LoginForm()
    params = {
        'form': form,
        'type': 'login',
    }

    if HttpMethod.get(): return render_template_auth('auth.html', **params)
    if form.invalid(): return render_template_auth('auth.html', **params)
    
    user = get_model('user').user_check(email=form.email.data, password=form.password.data)
    if not user: return render_template_auth('auth.html', **params)
    
    login_user(user, remember=True)
    Msg.success_msg('로그인 성공!')
    return redirect(url_for('views.home'))

@auth.route('/logout')
@login_required
def logout():
    logout_user() 
    Msg.success_msg('로그아웃 성공!')
    return redirect(url_for('views.home'))

@auth.route('/signup', methods=['GET', 'POST'])
@Deco.logout_required
def signup():
    form = SignUpForm()
    params = {
        'form': form,
        'type': 'signup',
    }

    if HttpMethod.get() or form.invalid(): return render_template_auth('auth.html', **params)
    if get_model('user').duplicate_check(email=form.email.data, username=form.username.data):
        return render_template_auth('auth.html', **params)
    
    get_model('user')( 
        username = form.username.data,
        email = form.email.data,
        password = form.password.data,
    ).add_instance()
    Msg.success_msg('회원가입 완료!')
    return redirect(url_for('views.home'))

@auth.route('/user-delete', methods=['DELETE'])
@login_required
def user_delete():
    user = get_model('user').get_instance_by_id_with(current_user.id)
    if not user: return Msg.delete_error()
    logout_user()
    
    user.delete_instance()
    return Msg.delete_success(f'{str(user)} 성공적으로 탈퇴하였습니다.')

# ------------------------------------------------ mypage, 이메일 인증 ------------------------------------------------
@auth.route('/mypage', methods=['GET', 'POST'])
@login_required
def mypage():
    Email.session_update()
    form = OtpForm()
    session_otp = Email.get_otp()
    remain_time = Email.get_remain_time()
    user_info_form = UserInfoForm()
    user_info_form.set_form_from_obj(current_user)
    params = {
        'otp':session_otp,
        'remain_time':remain_time,
        'form':form,
        'user_info_form':user_info_form,
    }
    
    if HttpMethod.get(): return render_template_auth('mypage.html', **params)
    if form.invalid(): return render_template_auth('mypage.html', **params)

    if form.otp.data != session_otp:
        Msg.error_msg('otp 비밀번호가 일치하지 않습니다.')
        return render_template_auth('mypage.html', **params)
    
    Email.delete_session()
    current_user.update_instance(create_permission=True)
    Msg.success_msg('이메일 인증 완료')
    return render_template_auth('mypage.html')

@auth.route('/send-mail-otp')
@Deco.login_and_not_have_create_permission_required
def send_mail_otp():
    try:
        Email.send_mail()
        Msg.success_msg('인증번호 전송 완료')
    except Exception as e:
        Msg.error_msg(str(e))
    return redirect(url_for('auth.mypage'))

@auth.route('/user-info-edit', methods=['POST'])
def user_info_edit():
    form = UserInfoForm()

    if form.valid() and not get_model('user').duplicate_check(username=form.username.data):  
        current_user.update_instance(username=form.username.data)
        Msg.success_msg('이름 수정 완료!')

    return redirect(url_for('auth.mypage'))

# ------------------------------------------------ third-party 가입 ------------------------------------------------
@auth.route('/<string:domain>/<string:type>')
@Deco.logout_required
def auth_page(domain, type):
    if ThirdParty.not_exist_domain(domain): return redirect(url_for(f'auth.{type}'))
    return redirect(ThirdParty.get_auth_url(domain=domain, type=type))

@auth.route('/callback/<string:domain>/<string:type>')
@Deco.logout_required
def callback(domain, type):
    access_token = ThirdParty.get_access_token(domain=domain, type=type)
    if access_token.status_code != 200:
        Msg.Msg.error_msg(f'ACCESS_TOKEN 에러 코드: {access_token.status_code}\n{access_token}')
        return redirect(url_for('views.home'))
    
    user_data = ThirdParty.get_user_info(access_token)
    print(user_data)
    if type == 'login':
        '''
            로그인
            1. 이메일 데이터 가져와서 db 체크
            2. login_user(user)
        '''
        email = user_data.get('email')
        user = get_model('user').get_instance_with(email=user_data['email'])
        if not user: return redirect(url_for('auth.login'))
        if not ThirdParty.domain_match(domain, user): return redirect(url_for('auth.login'))
        
        login_user(user, remember=True)
        Msg.success_msg('로그인 성공!')
        return redirect(url_for('views.home'))
    else:
        '''
            회원가입
            1. 이메일, 이름 데이터 가져오기 ('email', 'name')
            2. db 이메일 중복 체크
            3. auth_type = 도메인 저장. 
            4. 비밀번호는 랜덤 문자열 넣기 
        '''
        email = user_data['email']
        if get_model('user').duplicate_check(email=email): return redirect(url_for('auth.signup'))

        username = user_data.get('name', user_data.get('nickname'))
        username = get_model('user').make_new_name(username)
        get_model('user')(
            username=username,
            email=email,
            password=token_hex(16),
            create_permission=True,
            auth_type=ThirdParty.get_domain_num(domain),
        ).add_instance()
        Msg.success_msg('회원가입 완료!')
        return redirect(url_for('views.home'))
        
