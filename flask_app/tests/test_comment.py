import os
import sys
# 현재 스크립트의 부모 디렉터리를 상위로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


from flask_login import login_user, logout_user
from blog.models import db, get_model
from tests.test_base import TestBase
from bs4 import BeautifulSoup

class CommentTest(TestBase):
    name = 'COMMENT'

    # 매 시작 전 카테고리 추가
    def setUp(self):
        super().setUp()
        self.signUpAndLoginTwoUsers()
        self.create_post()
    
    # 매 종료 후 로그아웃
    def tearDown(self):
        logout_user()
        super().tearDown()

    # 유저 2명 생성 후 유저 1로 로그인
    def signUpAndLoginTwoUsers(self, post_create_permission=False):
        self.user1 = get_model('user')(
            username='11111',
            email='test1@example.com',
            password='123456',
            post_create_permission=post_create_permission,
        )
        db.session.add(self.user1)
        db.session.commit()
        self.user2 = get_model('user')(
            username='22222',
            email='test2@example.com',
            password='123456',
            post_create_permission=post_create_permission,
        )
        login_user(self.user1, remember=True)
    
    # post 생성
    def create_post(self):
        post = get_model('post')(
            title='test title',
            content='test content',
            category_id=2, # 'category 2'
            author_id=1
        )
        db.session.add(post)
        db.session.commit()


    '''
    1. comment 추가 확인
        사용자 2명 접속해서 댓글 내용 확인 + 수정, 삭제 버튼 확인
    '''
    def test_1_comment_add(self):
        # 1. 댓글 생성
        self.test_client.post('/comment-create/1', data=dict(content="test1"))
        self.assertEqual(get_model('comment').query.count(), 1) # db 확인

        # 2. 댓글 생성자 댓글 확인
        response = self.test_client.get('post/1')
        post_response = BeautifulSoup(response.data, 'html.parser')
        comment = post_response.find(id='commentList')
        self.assertIn('test1', comment.text) # 댓글 내용 확인
        self.assertIn('11111', comment.text) # 작성자 확인
        button = post_response.find(id='editAndDeleteButton') 
        self.assertIsNotNone(button) # 해당 id 존재해야함
        self.assertIsNotNone(button.find('i', {'class': 'fa-solid fa-pencil'})) # 수정 버튼
        self.assertIsNotNone(button.find('i', {'class': 'fa-solid fa-trash'})) # 수정 버튼

        # 3. 댓글 관찰자 댓글 확인
        logout_user() # 로그아웃
        login_user(self.user2, remember=True) # 다른 유저로 로그인
        response = self.test_client.get('post/1')
        post_response = BeautifulSoup(response.data, 'html.parser')
        comment = post_response.find(id='commentList')
        self.assertIn('test1', comment.text) # 댓글 내용 확인
        self.assertIn('11111', comment.text) # 작성자 확인
        button = post_response.find(id='editAndDeleteButton')
        self.assertIsNone(button) # 해당 id 없어야 함

    '''
    2. comment 수정 확인
        수정 modal 잘 뜨는지 확인
        수정 요청 날려서 확인(유저 2개 사용)
    '''
    def test_2_comment_edit(self):
        # 1. 댓글 생성
        response = self.test_client.post('/comment-create/1', data=dict(content="test1"), follow_redirects=True)

        # 2. modal 버튼 찾기
        modal_button = BeautifulSoup(response.data, 'html.parser').find('button', {'class': 'btn btn-secondary'})
        self.assertIsNotNone(modal_button)

        # 3. modal 들어가서 내용 확인
        modal_content = BeautifulSoup(response.data, 'html.parser').find('div', {'class':'modal fade'})
        self.assertEqual('Comment Edit', modal_content.find('h5', {'class': 'modal-title'}).text.strip())  # 모달 제목에 Comment Edit 표시
        self.assertEqual('test1', modal_content.find(id='commentContent')['value'].strip() ) # 모달 내용에 댓글 내용 표시

        # 4. 수정 요청 후 확인
        self.test_client.post('/comment-edit/1-1', data=dict(content="after_edit"))
        response = self.test_client.get('post/1')
        post_response = BeautifulSoup(response.data, 'html.parser')
        comment = post_response.find(id='commentList')
        self.assertNotIn('test1', comment.text) # 이 내용 없어야 됨
        self.assertIn('after_edit', comment.text) # 이 내용 있어야 됨
        self.assertIn('11111', comment.text) # 작성자 확인

        # 5. 다른 유저가 수정 요청 후 확인
        logout_user() # 로그아웃
        login_user(self.user2, remember=True) # 다른 유저로 로그인
        self.test_client.post('/comment-edit/1-1', data=dict(content="hacking_request"))
        response = self.test_client.get('post/1')
        post_response = BeautifulSoup(response.data, 'html.parser')
        comment = post_response.find(id='commentList')
        self.assertNotIn('hacking_request', comment.text) # 이 내용 없어야 됨
        self.assertIn('after_edit', comment.text) # 이 내용 있어야 됨


    '''
    3. comment 삭제 확인
        삭제 요청 후 확인(유저 2개 사용)
    '''
    def test_3_comment_delete(self):
        # 1. 댓글 생성
        self.test_client.post('/comment-create/1', data=dict(content="test1"))

        # 2. 삭제 요청 후 확인
        response = self.test_client.get('/comment-delete/1')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['message'], 'success')
        response = self.test_client.get('post/1')
        post_response = BeautifulSoup(response.data, 'html.parser')
        self.assertIsNone(post_response.find(id='commentList')) # commentWrapper 없어야 함
        self.assertIsNotNone(post_response.find(id='emptyComment')) # emptyComment 있어야 함


        # 3. 다른 유저 삭제 요청 후 확인
        self.test_client.post('/comment-create/1', data=dict(content="test1"))
        logout_user() # 로그아웃
        login_user(self.user2, remember=True) # 다른 유저로 로그인
        self.test_client.get('/comment-delete/1') # 삭제 요청
        response = self.test_client.get('post/1')
        post_response = BeautifulSoup(response.data, 'html.parser')
        self.assertIsNotNone(post_response.find(id='commentList')) # commentWrapper 있어야 함
        self.assertIsNone(post_response.find(id='emptyComment')) # emptyComment 없어야 함