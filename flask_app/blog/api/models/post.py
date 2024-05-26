from blog.api.models.base import BaseModel
from blog.api.models import get_db

db = get_db()

class Post(BaseModel):
    __tablename__ = 'post'                                                                          
    title = db.Column(db.String(150), nullable=False)                                               # 제목
    content = db.Column(db.Text, nullable=False)                                                    # 본문 내용
    
    author_id = db.Column(db.Integer, db.ForeignKey('user.id', name='fk_post_user', ondelete='CASCADE'), nullable=False)                
    user = db.relationship('User', back_populates='user_posts')             
        
    category_id = db.Column(db.Integer, db.ForeignKey('category.id', name='fk_post_category', ondelete='CASCADE'), nullable=False)   
    category = db.relationship('Category', back_populates='category_posts')    

    comments_count = db.Column(db.Integer, default=0)
    post_comments = db.relationship('Comment', back_populates='post', cascade='delete, delete-orphan', lazy='dynamic')
    files = db.relationship('File', back_populates='post', cascade='delete, delete-orphan', lazy='dynamic')

    def update_count(self):
        self.comments_count = self.post_comments.count()

    def before_new_flush(self):
        self.user.posts_count += 1

    def before_deleted_flush(self):
        self.user.posts_count -= 1

    def __repr__(self):
        return super().__repr__() + f'{self.title}'         

    def __str__(self):
        return super().__str__() + f'{self.title}'
    
# ------------------------------------------ Admin ------------------------------------------
from flask_login import current_user

from blog.api.models.base import AdminBase
from blog.api.forms import PostForm

class PostAdmin(AdminBase):
    # 1. 표시 할 열 설정
    column_list = ('id', 'title', 'content', 'date_created', 
        'user', 'category', 'comments_count')
    
    # 2. 폼 데이터 설정
    form = PostForm

    # 3. 현재 사용자 아이디 모델에 추가하기
    def on_model_change(self, form, model, is_created):
        model.author_id = current_user.id
        model.update_count()
        super().on_model_change(form, model, is_created)