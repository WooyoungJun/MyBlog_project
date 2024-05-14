import os
import sys

# 현재 스크립트의 부모 디렉터리를 상위로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from bs4 import BeautifulSoup

from blog.api.models import get_model
from tests.test_0_base import TestBase

class AuthTest(TestBase):
    name = 'AUTH'

    password = '123456'

    # 매 시작 전 카테고리 추가
    def setUp(self):
        super().setUp()
        self.signup()
        self.login()

    '''
    1. 로그인 로그아웃 기능 확인
        nav 메뉴 확인(로그인/로그아웃 상태에 따라 nav 메뉴 다름)
    '''
    def test_1_login_and_logout(self):
        # 1. Nav 에서 Login, Sign Up 버튼 없어야 하고, New Post, Logout 있어야 함
        response = self.test_client.get('/home')
        nav_after_login = BeautifulSoup(response.data, 'html.parser').nav
        self.assertNotIn('Login', nav_after_login.text)
        self.assertNotIn('Sign Up', nav_after_login.text)
        self.assertIn('New Post', nav_after_login.text)
        self.assertIn('Logout', nav_after_login.text)
    
        # 2. 로그아웃 후에 Nav 에서 Login, Sign Up 버튼 있어야하고, New Post, Logout 없어야 함
        self.logout()
        response = self.test_client.get('/home')
        nav_before_login = BeautifulSoup(response.data, 'html.parser').nav
        self.assertIn('Login', nav_before_login.text)
        self.assertIn('Sign Up', nav_before_login.text)
        self.assertNotIn('New Post', nav_before_login.text)
        self.assertNotIn('Logout', nav_before_login.text)

    '''
    2. 이메일 인증 기능 확인
        mypage 접근 후 otpSend 확인
        otp 이메일 보내고 otpInput 확인
        otp 입력 후 after_auth_info 확인
    '''
    def test_2_email_auth(self):
        # return True
        # 1. mypage 접근. otpSend 있어야하고 otpInput 없어야함.
        response = self.test_client.get('/auth/mypage')
        mypage_before_otp = BeautifulSoup(response.data, 'html.parser').find(id='user_info')
        self.assertIsNotNone(mypage_before_otp.find(id='otpSend'))
        self.assertIsNone(mypage_before_otp.find(id='otpInput'))

        # 2. otp 보내고 리디렉션 확인, otpInput 있어야하고 otpSend 없어야함.
        response = self.test_client.get('/auth/send-mail-otp', follow_redirects=True)
        mypage_after_otp = BeautifulSoup(response.data, 'html.parser')
        self.assertIsNone(mypage_after_otp.find(id='otpSend'))
        self.assertIsNotNone(mypage_after_otp.find(id='otpInput'))

        # 3. 이메일 인증 후 after_auth_info 확인
        self.user1.update_instance(create_permission=True)
        response = self.test_client.get('/auth/mypage')
        mypage_after_auth = BeautifulSoup(response.data, 'html.parser')
        self.assertIsNone(mypage_after_auth.find(id='otpSend'))
        self.assertIsNone(mypage_after_auth.find(id='otpInput'))
        self.assertIsNotNone(mypage_after_auth.find(id='after_auth_info'))

    '''
    3. 운영자 계정 확인
        운영자 X 접근 = 403 거부
        운영자 O 접근 = 접근 가능
        운영자 Post로 카테고리 생성
        카테고리 페이지 접근 후 확인
    '''
    def test_3_make_category(self):
        # 1. make-category 페이지 접근 = 권한 오류 = redirect 302
        response = self.test_client.get('/auth/make-category')
        self.assertEqual(response.status_code, 302)

        # 2. 권한 변경 후 확인
        self.user1.update_instance(admin_check=True)
        response = self.test_client.get('/auth/make-category')
        self.assertEqual(response.status_code, 200)

        # 3. 카테고리 추가 후 db에 적용 잘 됐는지 확인
        response = self.test_client.post('/auth/make-category', data=dict(
            name='category 1',
        ))
        self.assertEqual(get_model('category').get_instance_by_id_with(1).name, 'category 1')

        # 4. category 페이지 접속했을 때 카테고리 목록이 잘 출력되는지 확인
        response = self.test_client.get('/category')
        category_list = BeautifulSoup(response.data, 'html.parser').find(id='category_list')
        self.assertIn('category 1', category_list.text)

    '''
    4. 회원 탈퇴 기능
        로그인 후 회원 탈퇴 버튼 확인
        탈퇴 진행 후 로그인 시도
    '''
    def test_4_user_delete(self):
        # 1. 회원 탈퇴 버튼 확인
        response = self.test_client.get('/auth/mypage')
        mypage = BeautifulSoup(response.data, 'html.parser').find(id='user_info')
        self.assertIsNotNone(mypage.find(id='delete_button'))

        # 2. 회원 탈퇴
        response = self.test_client.delete('/auth/user-delete')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['message'], 'success')

        # 3. 로그인 확인, 실패 = 200 code
        response = self.test_client.post('/auth/login', data=dict(
            email=self.user1.email,
            password=self.password,
        ))
        self.assertEqual(response.status_code, 200)