import os
import sys
# 현재 스크립트의 부모 디렉터리를 상위로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask_login import login_user, logout_user
from blog.models import db, get_model
from tests.test_base import TestBase
from bs4 import BeautifulSoup

class PostTest(TestBase):
    name = 'POST'

    # 매 시작 전 카테고리 추가
    def setUp(self):
        super().setUp()
        self.add_categories()
    
    # 매 종료 후 로그아웃
    def tearDown(self):
        logout_user()
        super().tearDown()

    # 카테고리 2개 추가(category 1, category 2)
    def add_categories(self):
        db.session.add(get_model('category')(name='category 1'))
        db.session.commit()
        db.session.add(get_model('category')(name='category 2'))
        db.session.commit()

    # 회원가입(db에 직접 넣기) 후 로그인(login_user -> current_user 사용 가능)
    def signUpAndLogin(self, post_create_permission=False):
        user = get_model('user')(
            username='XXXXX',
            email='test@example.com',
            password='XXXXXX',
            post_create_permission=post_create_permission,
        )
        db.session.add(user)
        db.session.commit()
        login_user(user, remember=True)
        return user
    
    # post 생성
    def create_post(self):
        return self.test_client.post('/post-create', data=dict(
            title='test title',
            content='test content',
            category_id=2, # 'category 2'
            author_id=1
        ))

    ''' 
    1. 카테고리 생성
        db 직접 확인 + category 페이지 접속 후 확인
    '''
    def test_1_make_category(self):
        # 1. 카테고리 추가 후 db에 적용 잘 됐는지 확인
        self.assertEqual(get_model('category').query.filter_by(id=2).first().name, 'category 2')

        # 2. category 페이지 접속했을 때 카테고리 목록이 잘 출력되는지 확인
        response = self.test_client.get('/category')
        category_list = BeautifulSoup(response.data, 'html.parser')
        self.assertIn('category 1', category_list.text)
        self.assertIn('category 2', category_list.text)

    '''
    2. post 생성 페이지 접근 확인(로그인 전 + 후)
        로그인 전 => 홈으로 redirect = 302 code 체크
        로그인 후(권한 X) => abort => 홈으로 redirect = 302 code 체크
        로그인 후(권한 O) => 페이지 접근 가능 = 200 code 체크
        글 작성 시 category 목록 확인 => 개수 2개 = category 1, 2만 있어야 함
    '''
    def test_2_create_post_page(self):
        # 1. 로그인 전
        # 로그인 페이지 리다이렉트 = 302 code 체크
        response_before_login = self.test_client.get('/post-create')
        self.assertEqual(response_before_login.status_code, 302) 

        # 2. 회원 가입 + 로그인 후(글 권한 X) = abort = redirect 302 체크
        user = self.signUpAndLogin()
        response_create_post_page = self.test_client.get('/post-create')
        self.assertEqual(response_create_post_page.status_code, 302)

        # 3. 권한 변경 후 다시 시도
        user.post_create_permission = True
        db.session.commit()
        response_create_post_page = self.test_client.get('/post-create')
        self.assertEqual(response_create_post_page.status_code, 200)

        # 4. 카테고리 목록 확인
        category_list = BeautifulSoup(response_create_post_page.data, 'html.parser').find(id='category_id')
        self.assertEqual(len(category_list.find_all('option')), 2)
        self.assertIn('category 1', category_list.text)
        self.assertIn('category 2', category_list.text)

    '''
    3. post 생성
        post 생성 후 db 직접 체크
        post 페이지 직접 접근 후 제목, 저자, 카테고리, 본문 잘 나오는지 확인
        카테고리 접근 후 post가 해당 카테고리에 속했는지 확인
        default가 1이므로, category 2 생성 후 접근
    '''
    def test_3_after_create_post(self):
        # 1. 회원 가입 + 로그인 후 post 생성
        self.signUpAndLogin(post_create_permission=True)
        self.create_post()
        self.assertEqual(get_model('post').query.count(), 1) # db 체크

        # 2. post 페이지 접근 후 확인
        response_post_page = self.test_client.get('/post/1')
        source = BeautifulSoup(response_post_page.data, 'html.parser')
        self.assertIn('test title', source.find(id='title').text)
        self.assertIn('test content', source.find(id='content').text)
        self.assertIn('category 2', source.find(id='category').text)
        self.assertIn('XXXXX', source.find(id='author').text)

        # 3. 카테고리 접근 후 post 확인
        response_category_page = self.test_client.get('/posts-list/2')
        source = BeautifulSoup(response_category_page.data, 'html.parser')
        self.assertIn('category 2', source.find(id='category_wrapper').text)
        self.assertIn('test title', source.find(id='post_title').text)
        self.assertIn('총 1개', source.find(id='posts_count').text)
        self.assertIn('XXXXX', source.find(id='post_owner_name').text)

    '''
    4. post 수정
        post 생성 후 수정 페이지 2번 접근(저자 O, 저자 X)
        post 페이지 직접 접근 후 제목, 저자, 카테고리, 본문 잘 나오는지 확인
        카테고리 접근 후 post가 해당 카테고리에 속했는지 확인
    '''
    def test_4_update_post(self):
        # 1. 회원 가입 + 로그인 후 post 생성
        user1 = self.signUpAndLogin(post_create_permission=True)
        self.create_post()

        # 2. post 페이지 접근 후 수정 페이지 이동 (Edit, Delete 있어야 함)
        response_post_page = self.test_client.get('/post/1')
        source = BeautifulSoup(response_post_page.data, 'html.parser')
        self.assertIn('Edit', source.find(id='edit_button').text)
        self.assertIn('Delete', source.find(id='delete_button').text)
        response_edit_page = self.test_client.get('/post-edit/1')
        self.assertEqual(response_edit_page.status_code, 200)

        # 3. 수정 페이지에서 원본 데이터 출력 화인
        source = BeautifulSoup(response_edit_page.data, 'html.parser')
        self.assertIn('test title', source.find(id='title')['value']) # input 태그는 내부 값 X => value 값 꺼내야 함
        self.assertIn('test content', source.find(id='content').text)
        self.assertIn('category 2', source.find(id='category_id').find('option', selected=True).text)

        # 4. 수정 데이터 전송 후 확인
        self.test_client.post('/post-edit/1', data=dict(
            title='test title update',
            content='test content update',
            category_id=1, # 'category 1'
            author_id=1, # 'XXXXX'
        ))
        response_post_page = self.test_client.get('/post/1')
        source = BeautifulSoup(response_post_page.data, 'html.parser')
        self.assertIn('test title update', source.find(id='title').text)
        self.assertIn('test content update', source.find(id='content').text)
        self.assertIn('category 1', source.find(id='category').text)
        self.assertIn('XXXXX', source.find(id='author').text)
        logout_user()

        # 5. 저자 X 생성 후 로그인
        user2 = get_model('user')(
            username='XXXXO',
            email='test2@example.com',
            password='XXXXXX',
            post_create_permission=True,
        )
        db.session.add(user2)
        db.session.commit()
        login_user(user2, remember=True)

        # 6. 새로운 유저로 post 접근 후 edit 확인
        # read는 성공해야 하고 edit, delete 버튼 X
        response_post_page = self.test_client.get('/post/1')
        source = BeautifulSoup(response_post_page.data, 'html.parser')
        self.assertEqual(response_post_page.status_code, 200)
        self.assertIsNone(source.find(id='edit_button')) 
        self.assertIsNone(source.find(id='delete_button'))

        # 7. 새로운 유저로 post 수정 페이지 접근시 abort = redirect 302 확인
        response_edit_page = self.test_client.get('/post-edit/1')
        self.assertEqual(response_edit_page.status_code, 302)

    '''
    5. post 삭제
        post 생성 후 삭제 요청 2번(저자 O, 저자 X)
    '''
    def test_5_delete_post(self):
        # 1. 회원 가입 + 로그인 후 post 생성
        user1 = self.signUpAndLogin(post_create_permission=True)
        self.create_post()

        # 2. 포스트 삭제 요청 전송 후 확인(성공 = 200 code)
        response = self.test_client.get('/post-delete/1')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['message'], 'success')

        # 3. 삭제 포스트 접근 확인(redirect = 302 code)
        response = self.test_client.get('/post/1')
        self.assertEqual(response.status_code, 302)