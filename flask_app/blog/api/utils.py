from flask import abort, flash, jsonify, redirect, render_template, url_for, request
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
            Msg.error_msg('로그아웃 한 뒤 시도해주세요.')
            return redirect(url_for('views.home'))
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
            Msg.error_msg('이미 인증된 사용자입니다.')
            return redirect(url_for('views.home'))
        return f(*args, **kwargs)
    return decorated_function

def render_template_with_user(**context):
    context['user'] = current_user
    return render_template(**context)

# ------------------------------------------------- 소유자 확인, 메소드 체크, 폼 체크, 메세지, 에러 핸들러-------------------------------------------------
def is_owner(id):
    return id == current_user.id

class HttpMethod():
    @staticmethod
    def get():
        return request.method == 'GET'
    
    @staticmethod
    def post():
        return request.method == 'POST'
    
    @staticmethod
    def delete():
        return request.method == 'DELETE'
    
class Msg:
    @staticmethod
    def success_msg(msg):
        flash(msg, category="success")

    @staticmethod
    def error_msg(msg):
        flash(msg, category="error")

    @classmethod
    def delete_success(cls, msg):
        cls.success_msg(msg)
        return jsonify(message='success'), 200

    @classmethod
    def delete_error(cls, msg):
        cls.error_msg(msg)
        return jsonify(message='error'), 404

from flask import abort
def error(code):
    abort(code)