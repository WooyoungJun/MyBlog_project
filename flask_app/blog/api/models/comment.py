from blog.api.models.base import BaseModel
from blog.api.models import get_db
from .post import Post

db = get_db()

class Comment(BaseModel):
    __tablename__ = 'comment'
    content = db.Column(db.Text(), nullable=False)                                                  # 댓글 내용
    
    author_id = db.Column(db.Integer, db.ForeignKey('user.id', name='fk_comment_user', ondelete='CASCADE'), nullable=False)  
    user = db.relationship('User', back_populates="user_comments")

    post_id = db.Column(db.Integer, db.ForeignKey('post.id', name='fk_comment_post', ondelete='CASCADE'), nullable=False)  
    post = db.relationship('Post', back_populates='post_comments')

    def before_new_flush(self):
        self.user.comments_count += 1
        post = Post.get_instance_by_id_with(self.post_id)
        post.comments_count += 1

    def before_deleted_flush(self):
        self.user.comments_count -= 1
        self.post.comments_count -= 1

    def __repr__(self):
        return super().__repr__() + f'post_id: {self.post_id}, {self.content}'       

    def __str__(self):
        return super().__str__() + f'post_id: {self.post_id}, {self.content}'

# ------------------------------------------ Admin ------------------------------------------   
from wtforms import StringField, SelectField
from flask_login import current_user

from blog.api.models.base import AdminBase
from blog.api.forms import CommentForm

class CommentAdmin(AdminBase):
    # 1. 표시 할 열 설정
    column_list = ('id', 'content', 'date_created', 'user', 'post')

    # 2. 폼 데이터 설정
    form = type('ExtendedCommentForm', (CommentForm,), {
        'author_id': StringField('author', render_kw={'readonly': True}),
        'post_id': SelectField('post', choices=[])
    })
    
    # 3. 폼 데아터 채우기
    def create_form(self, obj=None):
        form = super().create_form(obj)
        form.author_id.data = current_user.username
        form.post_id.choices = [(post.id, str(post.id) + ': ' + post.title) for post in Post.get_all()]
        return form
    
    # 4. 수정 폼 설정
    def edit_form(self, obj):
        form = super().edit_form(obj)
        form.author_id.data = current_user.username
        post = Post.get_all(id=obj.post_id)
        form.post_id.choices = [(post.id, str(post.id) + ': ' + post.title)]
        return form

    # 4. 현재 사용자 아이디 모델에 추가하기
    def on_model_change(self, form, model, is_created):
        model.author_id = current_user.id
        super().on_model_change(form, model, is_created)