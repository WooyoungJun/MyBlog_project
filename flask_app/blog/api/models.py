from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import String, or_, func
from flask_login import UserMixin
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import selectinload, joinedload
from json import dumps
from random import randint

from .utils.etc import (
    Msg, get_korea_time, get_s3_config, make_new_file_name
)

db = SQLAlchemy()
migrate = Migrate()

def db_migrate_setup(app):
    db.init_app(app)
    migrate.init_app(app, db)
    with app.app_context():
        # db.Model 상속한 모든 클래스 추적해서 테이블 생성
        db.create_all()

def get_session():
    return db.session

# relationship(관계 맺는 모델 이름, back_populates=연결 필드 이름)
# Cascade = 1:N 관계에서 1쪽에 설정
# all = 모두
# save-update = session에 변경 add 시, 연결된 모든 객체도 session에 add
# delete = 삭제될 때만
# delete-orphan = delete + 관계가 끊길 때도 추가 삭제
# lazy='selectin': 주 객체를 가져오는 쿼리에 관련된 모든 객체를 가져오는 서브쿼리를 사용하여 즉시 로드
# lazy='dynamic': 지연로딩 설정 가능 = 쿼리 객체 반환 후 사용시 쿼리 실행됨
# 실제 사용할 때는 lazy='dynamic'설정 후 sqlalchemy.orm.selectinload 메소드 사용 = N+1 문제 해결

# ForeignKey(다른 테이블의 컬럼 이름, 삭제 옵션)
# db.backref => 반대쪽 모델에서 이 모델로 역참조 들어올 때, 타고 들어올 속성 명

# User <=> Post : 1:N 관계 -> Post(N) 쪽에 relationship 설정
# Category <=> Post : 1:N 관계 -> Post(N) 쪽에 relationship 설정
# Comment <=> User, Post : N:1 관계 -> Comment(N) 쪽에 relationship 설정


class BaseModel(db.Model):
    __abstract__ = True                                                             # 추상 클래스 설정
    id = db.Column(db.Integer, primary_key=True)                                    # primary key 설정
    date_created = db.Column(db.DateTime, default=get_korea_time())

    @classmethod
    def get_query(cls, id, **kwargs):
        return db.session.get(cls, id, **kwargs)
    
    @classmethod
    def query_with(cls, *args):
        return db.session.query(cls, *args)
    
    @staticmethod
    def commit():
        db.session.commit()
    
    @staticmethod
    def instance_check(instance):
        if not instance: Msg.error_msg('해당하는 인스턴스가 존재하지 않습니다.')

    @classmethod
    def get_options(cls, f, *relationships):
        return [f(getattr(cls, attr)) for attr in relationships]
    
    @classmethod
    def get_instance_by_id_with(cls, id, *relationships):
        options = cls.get_options(joinedload, *relationships)
        instance = cls.get_query(id, options=options)
        cls.instance_check(instance)
        return instance
    
    @classmethod
    def get_instance_with(cls, *relationships, **filter_conditions):
        options = cls.get_options(selectinload, *relationships)
        instance =  cls.query_with()\
            .filter_by(**filter_conditions).options(*options).first()
        cls.instance_check(instance)
        return instance
    
    @classmethod
    def get_all(cls):
        return cls.query_with().all() 
    
    @classmethod
    def get_all_by_ids(cls, ids):
        """
        주어진 id 리스트에 해당하는 객체들을 반환
        """
        ids = map(int, ids)
        return cls.query_with().filter(cls.id.in_(ids)).all()
    
    @classmethod
    def get_all_with(cls, *relationships, **filter_conditions):
        options = cls.get_options(selectinload, *relationships)
        return cls.query_with()\
            .filter_by(**filter_conditions).options(*options).all() 

    @classmethod
    def count_all(cls, *relationships, **filter_conditions):
        options = cls.get_options(selectinload, *relationships)
        return cls.query_with(func.count(cls.id))\
            .filter_by(**filter_conditions).options(*options).count()

    @classmethod
    def duplicate_check(cls, **kwargs):
        '''
        or 조건으로 묶어서 하나라도 존재하면 
        해당 필드 명시하고, True 반환
        중복 없으면 False 반환
        '''
        conditions = [func.lower(getattr(cls, key)) == func.lower(value) 
            if isinstance(getattr(cls, key).type, String) 
            else getattr(cls, key) == value 
            for key, value in kwargs.items()
        ]
        instances = cls.query_with().filter(or_(*conditions)).all()

        duplicate_fields = set()
        for instance in instances:
            for key, value in kwargs.items():
                if getattr(instance, key) == value:
                    duplicate_fields.add(key)

        if duplicate_fields:
            Msg.error_msg('중복된 정보가 존재합니다: {}'.format(', '.join(duplicate_fields)))
            return True
        return False

    def add_instance(self):
        db.session.add(self)
        self.commit()
        return self

    def update_instance(self, **kwargs):
        for key, value in kwargs.items():
            if key in self.__table__.columns:
                setattr(self, key, value)
        self.commit()

    def delete_instance(self):
        db.session.delete(self)
        self.commit()

    def fill_none_fields(self):
        none_fields = [field for field in self.__class__.__table__.columns if getattr(self, field.name) is None]
        for field in none_fields:
            setattr(self, field.name, field.default.arg)
    
    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
    
    def copy(self):
        new_item = self.__class__()
        for column in self.__table__.columns:
            setattr(new_item, column.name, getattr(self, column.name))
        return new_item
    
    def to_json(self):
        return dumps(self)

    def __repr__(self):
        return f'{self.__class__.__name__}: {self.id} '
    
    def __str__(self):
        return f'{self.__class__.__name__}: {self.id} '

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
    
    @classmethod
    def reset_all_limit(cls):
        cls.query_with().update({'file_upload_limit': 0.0})
        cls.commit()
    
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
                upload_size += get_model('file').upload_to_s3(file, post_id, self.id)
            except Exception as e:
                Msg.error_msg(str(e) + f'{file.filename} upload 실패')

        if upload_size == 0.0: return
        self.update_limit(upload_size)

    def __repr__(self):
        return super().__repr__() + f'{self.username}'         

    def __str__(self):
        return super().__str__() + f'{self.username}'                         
    
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
        user = get_model('user').get_instance_by_id_with(self.author_id)
        user.posts_count += 1

    def before_deleted_flush(self):
        self.user.posts_count -= 1

    def __repr__(self):
        return super().__repr__() + f'{self.title}'         

    def __str__(self):
        return super().__str__() + f'{self.title}'     
    
class File(BaseModel):
    __tablename__ = 'file'
    name = db.Column(db.String(150), nullable=False)
    size = db.Column(db.Float, nullable=False)

    author_id = db.Column(db.Integer, db.ForeignKey('user.id', name='fk_file_user', ondelete='CASCADE'), nullable=False)                
    user = db.relationship('User', back_populates='files')             
    
    post_id = db.Column(db.Integer, db.ForeignKey('post.id', name='fk_file_post', ondelete='CASCADE'), nullable=False)
    post = db.relationship('Post', back_populates='files')

    @classmethod
    def upload_to_s3(cls, file, post_id, author_id):
        '''
        file 인스턴스 추가 + s3에 업로드
        '''
        s3, s3_bucket_name, s3_default_dir = get_s3_config()

        new_file_name = make_new_file_name(file.filename, s3_default_dir)
        file_size = file.getbuffer().nbytes
        
        cls(
            name=new_file_name,
            size=file_size,
            post_id=post_id,
            author_id=author_id
        ).add_instance()
        
        s3.upload_fileobj(file, s3_bucket_name, s3_default_dir + new_file_name)
        file.close()
        return file_size

    def before_deleted_flush(self):
        s3, s3_bucket_name, s3_default_dir = get_s3_config()

        try:
            s3.delete_object(Bucket=s3_bucket_name, Key=s3_default_dir + self.name)
        except Exception as e:
            print('에러가 발생했습니다: ', str(e))

    def __repr__(self):
        return super().__repr__() + f'{self.name}'         

    def __str__(self):
        return super().__str__() + f'{self.name}' 

class Category(BaseModel):
    __tablename__ = 'category'                                                                      # 테이블 이름 명시적 선언
    name = db.Column(db.String(150), unique=True)                                                   # 메뉴 이름       
    category_posts = db.relationship('Post', back_populates='category', cascade='delete, delete-orphan', lazy='dynamic')             

    def __repr__(self):
        return super().__repr__() + f'{self.name}'         

    def __str__(self):
        return super().__str__() + f'{self.name}'    

class Comment(BaseModel):
    __tablename__ = 'comment'
    content = db.Column(db.Text(), nullable=False)                                                  # 댓글 내용
    
    author_id = db.Column(db.Integer, db.ForeignKey('user.id', name='fk_comment_user', ondelete='CASCADE'), nullable=False)  
    user = db.relationship('User', back_populates="user_comments")

    post_id = db.Column(db.Integer, db.ForeignKey('post.id', name='fk_comment_post', ondelete='CASCADE'), nullable=False)  
    post = db.relationship('Post', back_populates='post_comments')

    def before_new_flush(self):
        user = get_model('user').get_instance_by_id_with(self.author_id)
        post = get_model('post').get_instance_by_id_with(self.post_id)
        user.comments_count += 1
        post.comments_count += 1

    def before_deleted_flush(self):
        self.user.comments_count -= 1
        self.post.comments_count -= 1

    def __repr__(self):
        return super().__repr__() + f'post_id: {self.post_id}, {self.content}'       

    def __str__(self):
        return super().__str__() + f'post_id: {self.post_id}, {self.content}' 

class Message(BaseModel):
    __tablename__ = 'message'
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', name='fk_message_user', ondelete='CASCADE'), nullable=False)
    user = db.relationship('User', back_populates='user_messages')

    def __repr__(self):
        return super().__repr__() + f'user {self.user_id}\'s message \n{self.content}'       

    def __str__(self):
        return super().__str__() + f'user {self.user_id}\'s message \n{self.content}' 

def get_model(arg):
    models = {
        'user': User,
        'post': Post,
        'file': File,
        'category': Category,
        'comment': Comment,
        'message': Message,
    }
    return models[arg]

from sqlalchemy.event import listens_for
@listens_for(db.session, 'before_flush')
def before_flush(session, flush_context, instances):
    for obj in session.deleted:
        if hasattr(obj, 'before_deleted_flush'):
            obj.before_deleted_flush()
    
    for obj in session.new:
        if hasattr(obj, 'before_new_flush'):
            obj.before_new_flush()