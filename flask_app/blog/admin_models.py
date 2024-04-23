from flask import abort
from flask_admin.contrib.sqla import ModelView
from flask_admin.actions import action
from flask_login import current_user
from flask_wtf import FlaskForm
from werkzeug.security import generate_password_hash
from wtforms import BooleanField, StringField, SelectField
from blog.forms import CommentForm, SignUpForm, PostForm
from blog.models import get_model, db

class AdminBase(ModelView):
    def is_accessible(self):
        if current_user.is_authenticated == True and current_user.admin_check == True:
            return True
        else:
            return abort(403)
    column_formatters = {
        'date_created': lambda view, context, model, name: model.date_created.strftime('%Y-%m-%d %H:%M:%S')
    }

class UserAdmin(AdminBase):
    # 1. 표시 할 열 설정
    column_list = ('id', 'username', 'email', 'date_created', 'post_create_permission', 'admin_check', 'posts_count', 'comments_count')

    # 2. 폼 데이터 설정
    permisson_check = {
        'post_create_permission': BooleanField('post_create_permission', default=False), 
        'admin_check': BooleanField('admin_check', default=False)
    }
    create_form = type('ExtendedSignUpForm', (SignUpForm,), permisson_check)
    edit_form = type('EditForm', (FlaskForm,), permisson_check)

    # 3. 사용자가 패스워드를 입력하고 저장할 때 해시화하여 저장하는 로직 추가
    def on_model_change(self, form, model, is_created):
        if is_created:
            model.password = generate_password_hash(model.password)
        model.posts_count = model.user_posts.count()
        model.comments_count = model.user_comments.count()
        super().on_model_change(form, model, is_created)
    
    # 4사용자 지정 도구 추가
    @action('update_myinfo', 'Update My Info', 'Are you sure you want to update myinfo for selected users?')
    def update_myinfo(self, ids):
        # 선택된 사용자 목록 가져오기
        users = self.model.query.filter(self.model.id.in_(ids)).all()
        
        # 각 사용자에 대해 update_myinfo 메소드 실행
        for user in users:
            user.update_myinfo()

class PostAdmin(AdminBase):
    # 1. 표시 할 열 설정
    column_list = ('id', 'title', 'content', 'date_created', 'user', 'category', 'comments_count')
    
    # 2. 폼 데이터 설정
    form = PostForm

    # 3. 현재 사용자 아이디 모델에 추가하기
    def on_model_change(self, form, model, is_created):
        model.author_id = current_user.id
        model.comments_count = model.post_comments.count()
        super().on_model_change(form, model, is_created)

class CategoryAdmin(AdminBase):
    # 1. 표시 할 열 설정
    column_list = ('id', 'name')

    # 2. 폼 표시 X 열 설정
    form_excluded_columns = {'category_posts'} 

class CommentAdmin(AdminBase):
    # 1. 표시 할 열 설정
    column_list = ('id', 'content', 'date_created', 'author_id', 'post_id')

    # 2. 폼 데이터 설정
    form = type('ExtendedCommentForm', (CommentForm,), {
        'author_id': StringField('author', render_kw={'readonly': True}),
        'post_id': SelectField('post', choices=[])
    })
    
    # 3. 폼 데아터 채우기
    def create_form(self, obj=None):
        form = super().create_form(obj)
        form.author_id.data = current_user.username
        form.post_id.choices = [(post.id, str(post.id) + ': ' + post.title) for post in db.session.query(get_model('post')).all()]
        return form
    
    # 4. 수정 폼 설정
    def edit_form(self, obj):
        form = super().edit_form(obj)
        form.author_id.data = current_user.username
        post = db.session.get(get_model('post'), obj.post_id)
        form.post_id.choices = [(post.id, str(post.id) + ': ' + post.title)]
        return form

    # 4. 현재 사용자 아이디 모델에 추가하기
    def on_model_change(self, form, model, is_created):
        model.author_id = current_user.id
        super().on_model_change(form, model, is_created)

class MessageAdmin(AdminBase):
    # 1. 표시 할 열 설정
    column_list = ('id', 'content', 'user_id') 

    # 2. 폼 표시 X 열 설정
    form_excluded_columns = {'user_id', 'user'} 

    # 3. content 필드를 읽기 전용으로 표시
    def on_form_prefill(self, form, id):
        form.content.render_kw = {'readonly': 'readonly'}
    
    # 4. 생성 시 user_id 자동 채우기
    def on_model_change(self, form, model, is_created):
        model.user_id = current_user.id
        super().on_model_change(form, model, is_created)

def get_all_admin_models():
    return [[UserAdmin, get_model('user')], 
            [PostAdmin, get_model('post')], 
            [CategoryAdmin, get_model('category')], 
            [CommentAdmin, get_model('comment')],
            [MessageAdmin, get_model('message')]]