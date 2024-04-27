from flask import Blueprint, redirect, url_for
from .utils import error_msg

error = Blueprint('views', __name__)
# 403(Forbidden) 오류 발생 시 홈페이지로 리디렉션
@error.errorhandler(403)
def handle_forbidden_error(e):
    error_msg('권한이 없습니다')
    return redirect(url_for('views.home'))

# 404(Not Found) 오류 발생 시 홈페이지로 리디렉션
@error.errorhandler(404)
def handle_not_found_error(e):
    error_msg('잘못된 경로입니다.')
    return redirect(url_for('views.home'))

@error.route('/favicon.ico') 
def favicon(): 
    return url_for('static', filename='assets/favicon.ico')