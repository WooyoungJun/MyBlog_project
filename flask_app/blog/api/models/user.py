from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from random import randint

from blog.api.utils.etc import Msg
from blog.api.models import get_db
from blog.api.models.base import BaseModel
from blog.api.models.file import File

db = get_db()

FILE_UPLOAD_LIMIT = 5 * 1024 * 1024
# flask-login 사용하기 위해 UserMixin 상속
class User(BaseModel, UserMixin):
    __tablename__ = 'user'                                                          
    username = db.Column(db.String(150), unique=True)                               # username unique
    email = db.Column(db.String(150), unique=True)                                  # email unique
    password = db.Column(db.String(150))                                            # password 
    create_permission = db.Column(db.Boolean, default=False)                        # 글 작성 권한 여부
    admin_check = db.Column(db.Boolean, default=False)                              # 관리자 권한 여부
    auth_type = db.Column(db.Integer, default=0)                                    # 가입 type (0, 1, 2) = (홈페이지, 구글, 카카오)

    posts_count = db.Column(db.Integer, default=0)
    comments_count = db.Column(db.Integer, default=0)
    user_posts = db.relationship('Post', back_populates='user', cascade='delete, delete-orphan', lazy='dynamic')             
    user_comments = db.relationship('Comment', back_populates="user", cascade='delete, delete-orphan', lazy='dynamic') 
    user_messages = db.relationship('Message', back_populates='user', cascade='delete, delete-orphan', lazy='dynamic')     

    files = db.relationship('File', back_populates='user', cascade='delete, delete-orphan', lazy='dynamic')
    file_upload_limit = db.Column(db.Float, default=0.0)

    def __init__(self, password, **kwargs):
        self.set_password(password)
        super().__init__(**kwargs)
    
    def set_password(self, password):
        self.password = generate_password_hash(password)
    
    @classmethod
    def user_check(cls, email, password):
        email = email.strip().replace(' ', '')
        user = cls.query_with().filter_by(email=email).first()
        if user:
            if not check_password_hash(password, user.password): return user
            else: return Msg.error_msg('비밀번호가 틀렸습니다.')
        else: return Msg.error_msg('가입되지 않은 이메일입니다.')

    @classmethod
    def make_new_name(cls, name):
        new_name = name
        while cls.is_in_model(username=new_name):
            random_number = randint(100000, 999999)
            new_name = name + str(random_number)
        return new_name
    
    @classmethod
    def is_in_model(cls, **kwargs):
        return cls.query_with().filter_by(**kwargs).first() is not None

    def update_count(self):
        self.posts_count = self.user_posts.count()
        self.comments_count = self.user_comments.count()
    
    def have_create_permission(self):
        return self.create_permission
    
    def have_admin_check(self):
        return self.admin_check
    
    # ---------------------- file 관련 ----------------------
    @classmethod
    def reset_all_limit(cls):
        cls.query_with().update({'file_upload_limit': 0.0})
        cls.commit()

    def get_limit(self):
        if self.can_upload():
            return FILE_UPLOAD_LIMIT - self.file_upload_limit
        else:
            return 0.0
    
    def can_upload(self):
        return self.file_upload_limit < FILE_UPLOAD_LIMIT
    
    def update_limit(self, upload_size):
        self.file_upload_limit += upload_size
        self.commit()

    def upload_files(self, files, post_id):
        '''
        파일들 객체 생성 + s3에 업로드 + 일일 할당량 업데이트
        '''
        if self.get_limit() < sum(file.getbuffer().nbytes for file in files):
            Msg.error_msg('일일 파일 업로드 할당량을 초과하였습니다.')
            files = None

        if not files or not files[0]: return

        upload_size = 0.0
        for file in files:
            try:
                upload_size += File.upload_to_s3(file, post_id, self.id)
            except Exception as e:
                Msg.error_msg(str(e) + f'{file.filename} upload 실패')

        if upload_size == 0.0: return
        self.update_limit(upload_size)
    
    def __repr__(self):
        return super().__repr__() + f'{self.username}'         

    def __str__(self):
        return super().__str__() + f'{self.username}' 

# ------------------------------------------ Admin ------------------------------------------
from wtforms import BooleanField, StringField
from flask_login import current_user

from blog.api.models.base import AdminBase
from blog.api.forms import SignUpForm, FlaskForm

class UserAdmin(AdminBase):
    # 1. 표시 할 열 설정
    column_list = ('id', 'username', 'email', 
        'create_permission', 'admin_check', 'posts_count', 'comments_count', 
        'auth_type', 'file_upload_limit',
    )

    # 2. 폼 데이터 설정
    permisson_check = {
        'username': StringField('username'),
        'create_permission': BooleanField('create_permission', default=False), 
        'admin_check': BooleanField('admin_check', default=False),
        # 'auth_type': IntegerField('auth_type', default=0),
    }
    create_form = type('ExtendedSignUpForm', (SignUpForm,), permisson_check)
    edit_form = type('EditForm', (FlaskForm,), permisson_check)

    # 3. 사용자가 패스워드를 입력하고 저장할 때 해시화하여 저장하는 로직 추가
    def on_model_change(self, form, model, is_created):
        if is_created:
            model.set_password(form.password)
        model.update_count()
        super().on_model_change(form, model, is_created)
    
    # 4. 자신 계정 삭제 불가
    def delete_model(self, model):
        if model.id == current_user.id:
            Msg.error_msg('자신의 계정은 삭제할 수 없습니다.')
            return
        super().delete_model(model)
