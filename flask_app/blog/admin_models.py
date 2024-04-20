from flask import abort
from flask_admin.contrib.sqla import ModelView
from flask_login import current_user
from werkzeug.security import generate_password_hash
from wtforms import BooleanField
from blog.forms import SignUpForm, PostForm
from blog.models import get_model

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
    column_list = ('id', 'username', 'email', 'date_created', 'post_create_permission', 'admin_check')

    # 2. 폼 데이터 설정
    form = type('ExtendedSignUpForm', (SignUpForm,), {
            'post_create_permission': BooleanField('post_create_permission', default=False), 
            'admin_check': BooleanField('admin_check', default=False)
            })

    # 3. 사용자가 패스워드를 입력하고 저장할 때 해시화하여 저장하는 로직 추가
    def on_model_change(self, form, model, is_created):
        model.password = generate_password_hash(form.password.data)
        super().on_model_change(form, model, is_created)

class PostAdmin(AdminBase):
    # 1. 표시 할 열 설정
    column_list = ('id', 'title', 'content', 'date_created', 'user', 'category')
    
    # 2. 폼 데이터 설정
    form = PostForm

    # 3. 현재 사용자 아이디 모델에 추가하기
    def on_model_change(self, form, model, is_created):
        model.author_id = current_user.id
        super().on_model_change(form, model, is_created)

class CategoryAdmin(AdminBase):
    # 1. 표시 할 열 설정
    column_list = ('id', 'name')

    # 2. 폼 표시 X 열 설정
    form_excluded_columns = {'category_posts'} 

class CommentAdmin(AdminBase):
    # 1. 표시 할 열 설정
    column_list = ('id', 'content', 'date_created', 'author_id', 'post_id')

def get_all_admin_models():
    return [[UserAdmin, get_model('user')], [PostAdmin, get_model('post')], [CategoryAdmin, get_model('category')], [CommentAdmin, get_model('comment')]]