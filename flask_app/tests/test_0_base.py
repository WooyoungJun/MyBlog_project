import os
import sys
# 현재 스크립트의 부모 디렉터리를 상위로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
from flask_login import login_user, logout_user

from blog.factory import create_app
from blog.api.models import db, get_model
from tests.test_config import TestConfig

class TestBase(unittest.TestCase):
    name = 'BASE'
    
    # 해당 테스트 클래스 실행 시 최초 1번 실행
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = create_app(config=TestConfig, mode='TEST') # Flask app 생성
        cls.app_context = cls.app.app_context() # app context 
        cls.app_test_request_context = cls.app.test_request_context() # test request context
        cls.test_client = cls.app.test_client() # test client 생성
        return print(f'{cls.name} Test Start')

    @classmethod
    def tearDownClass(cls) -> None:
        return print(f'{cls.name} Test End')
    
    def setUp(self):
        # 테스트 실행 전 Set Up 코드
        # app context 
        self.app_context.push()
        self.app_test_request_context.push()
        with self.app_context:
            db.create_all()
        self.user1 = get_model('user')(
            username='11111',
            email='test1@example.com',
            password='123456',
        )
        self.user2 = get_model('user')(
            username='22222',
            email='test2@example.com',
            password='123456',
        )

    def tearDown(self):
        # 테스트 실행 후 Set Down 코드
        # 세션 삭제 및 데이터베이스 초기화
        logout_user()
        db.session.remove()
        db.drop_all()
        self.app_test_request_context.pop()
        self.app_context.pop()

    user1 = get_model('user')(
        username='11111',
        email='test1@example.com',
        password='123456',
    )

    user2 = get_model('user')(
        username='22222',
        email='test2@example.com',
        password='123456',
    )

    def signup(self, create_permission=False):
        self.user1.create_permission = create_permission
        self.user2.create_permission = create_permission
        self.user1.add_instance()
        self.user2.add_instance()

    def login(self, user_num=1):
        login_user(getattr(self, f'user{user_num}'), remember=True)

    def logout(self):
        logout_user()