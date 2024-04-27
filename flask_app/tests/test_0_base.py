import os
import sys
# 현재 스크립트의 부모 디렉터리를 상위로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import unittest

from blog import create_app
from blog.models import db
from tests.test_config import TestConfig

class TestBase(unittest.TestCase):
    name = 'BASE'

    # 해당 테스트 클래스 실행 시 최초 1번 실행
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = create_app(config=TestConfig, mode='DEVELOPMENT') # Flask app 생성
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

    def tearDown(self):
        # 테스트 실행 후 Set Down 코드
        # 세션 삭제 및 데이터베이스 초기화
        db.session.remove()
        db.drop_all()
        self.app_test_request_context.pop()
        self.app_context.pop()