from flask import abort, flash, redirect, render_template, url_for, request
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
            error_msg('로그아웃 한 뒤 시도해주세요.')
            return redirect(url_for('views.home'))
        return f(*args, **kwargs)
    return decorated_function

def only_post_method(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not post_method(): return abort(405)
        return f(*args, **kwargs)
    return decorated_function

def only_delete_method(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not delete_method(): return abort(405)
        return f(*args, **kwargs)
    return decorated_function

def only_patch_method(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not patch_method(): return abort(405)
        return f(*args, **kwargs)
    return decorated_function

def create_permission_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.have_create_permission(): return abort(403)
        return f(*args, **kwargs)
    return decorated_function

def not_have_create_permission_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if current_user.have_create_permission(): 
            error_msg('이미 인증된 사용자입니다.')
            return redirect(url_for('views.home'))
        return f(*args, **kwargs)
    return decorated_function

def render_template_with_user(**context):
    context['user'] = current_user
    return render_template(**context)

# ------------------------------------------------- 소유자 확인, 메소드 체크, 폼 체크, 메세지, 에러 핸들러-------------------------------------------------
def is_owner(id):
    return id == current_user.id

def get_method():
    return request.method == 'GET'

def post_method():
    return request.method == 'POST'

def delete_method():
    return request.method == 'DELETE'

def patch_method():
    return request.method == 'PATCH'

def form_invalid(form):
    if not form.validate_on_submit():
        error_msg('유효성 검사 실패.')
        return True

def form_valid(form):
    return form.validate_on_submit()
    
def success_msg(msg):
    flash(msg, category="success")

def error_msg(msg):
    flash(msg, category="error")

from flask import abort
def error(code):
    abort(code)