from flask import redirect, render_template, url_for
from flask_login import login_required, current_user
from functools import wraps

from .etc import Msg
from .error import Error

class Deco():
    @staticmethod
    def login_and_admin_required(f):
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            if not current_user.have_admin_check(): return Error.error(403)
            return f(*args, **kwargs)
        return decorated_function

    @staticmethod
    def logout_required(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if current_user.is_authenticated:
                Msg.error_msg('로그아웃 한 뒤 시도해주세요.')
                return redirect(url_for('views.home'))
            return f(*args, **kwargs)
        return decorated_function

    @staticmethod
    def login_and_create_permission_required(f):
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            if not current_user.have_create_permission(): return Error.error(403)
            return f(*args, **kwargs)
        return decorated_function

    @staticmethod
    def login_and_not_have_create_permission_required(f):
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            if current_user.have_create_permission(): 
                Msg.error_msg('이미 인증된 사용자입니다.')
                return redirect(url_for('views.home'))
            return f(*args, **kwargs)
        return decorated_function

    @staticmethod
    def render_template_with_user(**context):
        context['user'] = current_user
        return render_template(**context)