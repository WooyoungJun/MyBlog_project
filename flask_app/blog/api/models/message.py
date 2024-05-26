from blog.api.models.base import BaseModel
from blog.api.models import get_db

db = get_db()

class Message(BaseModel):
    __tablename__ = 'message'
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', name='fk_message_user', ondelete='CASCADE'), nullable=False)
    user = db.relationship('User', back_populates='user_messages')

    def __repr__(self):
        return super().__repr__() + f'user {self.user_id}\'s message \n{self.content}'       

    def __str__(self):
        return super().__str__() + f'user {self.user_id}\'s message \n{self.content}'

# ------------------------------------------ Admin ------------------------------------------   
from flask_login import current_user

from blog.api.models.base import AdminBase

class MessageAdmin(AdminBase):
    # 1. 표시 할 열 설정
    column_list = ('id', 'content', 'user') 

    # 2. 폼 표시 X 열 설정
    form_excluded_columns = {'user_id', 'user'} 

    # 3. content 필드를 읽기 전용으로 표시
    def on_form_prefill(self, form, id):
        form.content.render_kw = {'readonly': 'readonly'}
    
    # 4. 생성 시 user_id 자동 채우기
    def on_model_change(self, form, model, is_created):
        model.user_id = current_user.id
        super().on_model_change(form, model, is_created)