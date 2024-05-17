import time
from email.mime.text import MIMEText
from random import randint
from flask_login import current_user
import asyncio

class Email():
    @classmethod
    def init_app(cls, app, session):
        cls.app = app
        cls.config = app.config
        cls.session = session

    @classmethod
    def send_mail(cls):
        otp = str(randint(100000, 999999))
        msg = MIMEText(f'MyBlog 회원가입 \n인증번호를 입력하여 이메일 인증을 완료해 주세요.\n인증번호 :{otp}')
        msg['Subject'] = '[MyBlog 이메일 인증]'

        asyncio.gather(cls.smtp_send_mail_async(msg))
        print('otp 이메일 전송 요청 완료!')

        cls.session[f'otp_{current_user.email}'] = otp  # 세션에 인증번호 저장
        cls.session[f'time_{current_user.email}'] = int(time.time()) + cls.config['MAIL_LIMIT_TIME']  # 인증번호 제한 시간

    @classmethod
    async def smtp_send_mail_async(cls, msg):
        from smtplib import SMTP
        config = cls.config
        smtp = SMTP(host=config['MAIL_SERVER'], port=config['MAIL_PORT'])
        await smtp.starttls() # TLS 암호화 보안 연결 설정
        await smtp.login(config['MAIL_USERNAME'], config['MAIL_PASSWORD'])
        await smtp.sendmail(config['MAIL_USERNAME'], current_user.email, msg.as_string())
        smtp.quit()
        print('otp 이메일 전송 처리 완료!')

    @classmethod
    def delete_error_email(cls, app):
        with app.app_context():
            asyncio.gather(cls.imap_delete_error_mail())
            print('쌓인 에러 메세지 삭제 요청 완료!')

    @classmethod
    async def imap_delete_error_mail(cls):
        from imaplib import IMAP4_SSL
        config = cls.config
        imap = IMAP4_SSL('imap.gmail.com')
        await imap.login(config['MAIL_USERNAME'], config['MAIL_PASSWORD'])
        await imap.select('inbox')
        status, email_ids = await imap.search(None, '(FROM "mailer-daemon@googlemail.com")')
        if status == 'OK':
            email_ids = email_ids[0].split()
            for email_id in email_ids:
                await imap.store(email_id, '+FLAGS', '\\Deleted')
        await imap.expunge() # deleted 플래그 모두 삭제

        imap.close() # 세션 종료
        imap.logout() # 연결 해제
        print('쌓인 에러 메세지 삭제 처리 완료!')

    @classmethod
    def session_update(cls):
        session_otp = cls.get_otp()
        if not session_otp: return None
        if cls.get_remain_time() < 0: cls.delete_session()

    @classmethod
    def delete_session(cls):
        try:
            cls.session.pop(f'otp_{current_user.email}')
            cls.session.pop(f'time_{current_user.email}')
        except:
            return

    @classmethod
    def get_otp(cls):
        return cls.session.get(f'otp_{current_user.email}')

    @classmethod
    def get_time(cls):
        return cls.session.get(f'time_{current_user.email}')

    @classmethod
    def get_remain_time(cls):
        session_time = cls.get_time()
        if not session_time: return None
        return session_time - int(time.time())