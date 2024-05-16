from flask import abort, redirect, url_for

from .etc import Msg

def error(code):
    abort(code)
    
def error_handler_setting(app):
    @app.errorhandler(400)
    def handle_bad_request_error(e):
        Msg.error_msg('잘못된 요청입니다.')
        return redirect(url_for('views.home'))

    @app.errorhandler(401)
    def handle_unauthorized_error(e):
        Msg.error_msg('인증이 필요합니다.')
        return redirect(url_for('views.home'))

    @app.errorhandler(403)
    def handle_forbidden_error(e):
        Msg.error_msg('권한이 없습니다.')
        return redirect(url_for('views.home'))

    @app.errorhandler(404)
    def handle_not_found_error(e):
        Msg.error_msg('요청한 페이지를 찾을 수 없습니다.')
        return redirect(url_for('views.home'))

    @app.errorhandler(405)
    def handle_method_not_allowed_error(e):
        Msg.error_msg('허용되지 않은 HTTP 메소드입니다.')
        return redirect(url_for('views.home'))

    @app.errorhandler(500)
    def handle_internal_server_error(e):
        Msg.error_msg('서버에서 오류가 발생했습니다.')
        return redirect(url_for('views.home'))

    @app.route('/favicon.ico') 
    def favicon(): 
        return url_for('static', filename='assets/favicon.ico')