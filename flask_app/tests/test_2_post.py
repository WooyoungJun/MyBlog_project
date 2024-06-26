import os
import sys
# 현재 스크립트의 부모 디렉터리를 상위로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from bs4 import BeautifulSoup

from blog.api.models import get_model
from tests.test_0_base import TestBase

class PostTest(TestBase):
    name = 'POST'

    # 매 시작 전 카테고리 추가
    def setUp(self):
        super().setUp()
        get_model('category')(name='category 1').add_instance()
        get_model('category')(name='category 2').add_instance()
        self.signup(create_permission=True)
        self.login()
        self.post = get_model('post')(
            title='test title', 
            content='test content', 
            category_id=2, 
            author_id=1,
        )
        self.post.add_instance()

    '''
    1. post 생성
        post 생성 후 db 직접 체크
        post 페이지 직접 접근 후 제목, 저자, 카테고리, 본문 잘 나오는지 확인
        카테고리 접근 후 post가 해당 카테고리에 속했는지 확인
        default가 1이므로, category 2 생성 후 접근
    '''
    def test_1_after_create_post(self):
        # 1. post 개수 확인
        self.assertEqual(get_model('post').count_all(), 1)

        # 2. post 페이지 접근 후 확인
        response_post_page = self.test_client.get('/post/1')
        source = BeautifulSoup(response_post_page.data, 'html.parser')
        self.assertIn(self.post.title, source.find(id='title').text)
        self.assertIn(self.post.content, source.find(id='content').text)
        self.assertIn(str(self.post.category_id), source.find(id='category').attrs['name'])
        self.assertIn(str(self.post.author_id), source.find(id='author').attrs['name'])

        # 3. 카테고리 접근 후 post 확인
        response_category_page = self.test_client.get('/posts-list/2')
        source = BeautifulSoup(response_category_page.data, 'html.parser')
        self.assertIn(self.post.title, source.find(id='post_title').text)
        self.assertIn('총 1개', source.find(id='posts_count').text)
        self.assertIn(str(self.post.category_id), source.find(id='category_wrapper').attrs['name'])
        self.assertIn(str(self.post.author_id), source.find(id='post_owner_name').attrs['name'])

    '''
    2. post 수정
        post 생성 후 수정 페이지 2번 접근(저자 O, 저자 X)
        post 페이지 직접 접근 후 제목, 저자, 카테고리, 본문 잘 나오는지 확인
        카테고리 접근 후 post가 해당 카테고리에 속했는지 확인
    '''
    def test_2_update_post(self):
        # 1. post 페이지 접근 후 수정 페이지 이동 (Edit, Delete 있어야 함)
        response_post_page = self.test_client.get('/post/1')
        source = BeautifulSoup(response_post_page.data, 'html.parser')
        self.assertIn('Edit', source.find(id='edit_button').text)
        self.assertIn('Delete', source.find(id='delete_button').text)
        response_edit_page = self.test_client.get('/post-edit/1')
        self.assertEqual(response_edit_page.status_code, 200)

        # 2. 수정 페이지에서 원본 데이터 출력 화인
        source = BeautifulSoup(response_edit_page.data, 'html.parser')
        self.assertIn(self.post.title, source.find(id='title')['value']) # input 태그는 내부 값 X => value 값 꺼내야 함
        self.assertIn(self.post.content, source.find(id='content').text)
        self.assertIn(str(self.post.category_id), source.find(id='category_id').find('option', selected=True)['value'])

        # 3. 수정 데이터 전송 후 확인
        self.test_client.post('/post-edit/1', data=dict(
            title='test title update',
            content='test content update',
            category_id=1, # 'category 1'
            author_id=1, # 'XXXXX'
        ))
        response_post_page = self.test_client.get('/post/1')
        source = BeautifulSoup(response_post_page.data, 'html.parser')
        self.assertIn(self.post.title, source.find(id='title').text)
        self.assertIn(self.post.content, source.find(id='content').text)
        self.assertIn(str(self.post.category_id), source.find(id='category').attrs['name'])
        self.assertIn(str(self.post.author_id), source.find(id='author').attrs['name'])
        self.logout()

        # 5. 저자 X 생성 후 로그인
        self.login(2)

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
    3. post 삭제
        post 생성 후 삭제 요청 2번(저자 O, 저자 X)
    '''
    def test_3_delete_post(self):
        # 1. 포스트 삭제 요청 전송 후 확인(성공 = 200 code)
        response = self.test_client.delete('/post-delete/1')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['message'], 'success')

        # 2. 삭제 포스트 접근 확인(Not Found = redirect 302)
        response = self.test_client.get('/post/1')
        self.assertEqual(response.status_code, 302)