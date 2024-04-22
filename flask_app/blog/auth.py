from flask import Blueprint, request, redirect, render_template, flash, url_for
from flask_login import current_user, login_required, login_user, logout_user
from werkzeug.security import check_password_hash
from .forms import LoginForm, SignUpForm
from .models import db, get_model

auth = Blueprint('auth', __name__)
BASE_AUTH_DIR = 'auth/'

@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if request.method == 'POST' and form.validate_on_submit():
        user = get_model('user').query.filter_by(email=form.email.data).first()
        
        # 이메일로 유저 체크
        if not user:
            flash('가입되지 않은 이메일입니다.', category="error")
        # 비밀번호 체크
        elif check_password_hash(form.password.data, user.password):
            flash('비밀번호가 틀렸습니다.', category="error")
        else:
            flash('로그인 성공!', category="success")
            login_user(user, remember=True) # 로그인 처리, session에 저장
            return redirect(url_for('views.home')) # 홈으로 이동
    else: # GET 요청 or form invalidated
        return render_template(BASE_AUTH_DIR + 'auth.html', form=form, user=current_user, title_name='Login')

@auth.route('/logout')
@login_required # 로그인 상태 체크
def logout():
    logout_user() # session에서 삭제
    flash('로그아웃 성공!', category="success")
    return redirect(url_for('views.home')) # 홈으로 이동

@auth.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    form = SignUpForm()
    if request.method == 'POST' and form.validate_on_submit():
        user = get_model('user')( 
            username = form.username.data,
            email = form.email.data,
            password = form.password.data,
        )
        
        email_check = get_model('user').query.filter_by(email=user.email).first()
        username_check = get_model('user').query.filter_by(username=user.username).first()

        if email_check:
            flash('이미 존재하는 이메일입니다.', category="error")
        elif username_check:
            flash('이미 존재하는 이름입니다.', category="error")
        else:
            db.session.add(user)
            db.session.commit() # 변화 적용
            flash('회원가입 완료!', category="success")
            return redirect(url_for('views.home')) # 홈으로 이동
    return render_template(BASE_AUTH_DIR + 'auth.html', form=form, user=current_user, title_name="Sign Up")