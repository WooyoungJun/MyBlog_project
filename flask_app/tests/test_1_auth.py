import os
import sys
# 현재 스크립트의 부모 디렉터리를 상위로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from flask_login import login_user
from bs4 import BeautifulSoup

from blog.models import get_model
from tests.test_0_base import TestBase

class AuthTest(TestBase):
    name = 'AUTH'

    user = dict(
        username='11111',
        email='test1@example.com',
        password='123456',
        password_check='123456',
    )

    def signup(self, user_num):
        return self.test_client.post('/auth/sign-up', data=getattr(self, f'user{user_num}'))

    '''
    1. 회원 가입 기능 확인 
        web 통해서 회원 가입
        redirect = 302 code & db 유저 수 확인
    '''
    def test_1_signup_web(self):
        response = self.test_client.post('/auth/sign-up', data=dict(
            username=self.user['username'],
            email=self.user['email'],
            password=self.user['password'],
            password_check=self.user['password_check'],
        ))
        self.assertEqual(response.status_code, 302) # 성공 시 redirect = code 302
        self.assertEqual(get_model('user').count_all(), 1)     # 유저 수 확인

    '''
    2. 로그인 기능 확인
        회원가입 하고 로그인 진행
        회원가입 로그인 모두 redirect = 302 code 받으면 성공
        nav 메뉴 확인(로그인/로그아웃 상태에 따라 nav 메뉴 다름)
    '''
    def test_2_login(self):
        # 1. 로그인 전에 Nav 에서 Login, Sign Up 버튼 있어야하고, New Post, Logout 없어야 함
        response = self.test_client.get('/home')
        nav_before_login = BeautifulSoup(response.data, 'html.parser').nav

        self.assertIn('Login', nav_before_login.text)
        self.assertIn('Sign Up', nav_before_login.text)
        self.assertNotIn('New Post', nav_before_login.text)
        self.assertNotIn('Logout', nav_before_login.text)

        # 2. 회원 가입 진행
        user = get_model('user')(
            username=self.user['username'],
            email=self.user['email'],
            password=self.user['password']
        )
        user.add_instance()

        # 3. 로그인 진행
        response = self.test_client.post('/auth/login', data=dict(
                email=self.user['email'],
                password=self.user['password'],
            ), follow_redirects=True)

        # 4. Nav 에서 Login, Sign Up 버튼 없어야 하고, New Post, Logout 있어야 함
        nav_after_login = BeautifulSoup(response.data, 'html.parser').nav
        self.assertNotIn('Login', nav_after_login.text)
        self.assertNotIn('Sign Up', nav_after_login.text)
        self.assertIn('New Post', nav_after_login.text)
        self.assertIn('Logout', nav_after_login.text)
    
    '''
    3. 로그아웃 기능 확인
        회원가입 하고 로그인 -> 로그아웃 진행
        회원가입 로그인 모두 redirect = 302 code 받으면 성공
        nav 메뉴 확인(로그인/로그아웃 상태에 따라 nav 메뉴 다름)
    '''
    def test_3_logout(self):

        # 1. 회원가입
        user = get_model('user')(
            username=self.user['username'],
            email=self.user['email'],
            password=self.user['password']
        )
        user.add_instance()

        # 2. 로그인
        login_user(user, remember=True)

        # 3. 로그아웃
        response = self.test_client.get('/auth/logout', follow_redirects=True)

        # 4. Nav 에서 Login, Sign Up 버튼 있어야하고, New Post, Logout 없어야 함
        nav_after_logout = BeautifulSoup(response.data, 'html.parser').nav
        self.assertIn('Login', nav_after_logout.text)
        self.assertIn('Sign Up', nav_after_logout.text)
        self.assertNotIn('New Post', nav_after_logout.text)
        self.assertNotIn('Logout', nav_after_logout.text)