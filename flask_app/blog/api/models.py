from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import String, or_, func
from flask_login import UserMixin
from flask_migrate import Migrate
from datetime import datetime, timedelta, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import selectinload, joinedload

from .utils import error_msg
from os.path import exists

# 한국 시간대 오프셋(UTC+9)을 생성합니다.
KST_offset = timezone(timedelta(hours=9))

db = SQLAlchemy()
migrate = Migrate()

def db_migrate_setup(app):
    db.init_app(app)
    migrate.init_app(app, db)
    with app.app_context():
        # db.Model 상속한 모든 클래스 추적해서 테이블 생성
        db.create_all()

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
    
    @classmethod
    def get_instance_by_id(cls, id):
        instance = db.session.get(cls, id)
        if not instance:
            error_msg('해당하는 인스턴스가 존재하지 않습니다.')
        return instance
    
    @classmethod
    def get_instance_by_id_with(cls, id, *relationships):
        options = [joinedload(getattr(cls, attr)) for attr in relationships]
        instance = db.session.get(cls, id, options=options)
        if not instance:
            error_msg('해당하는 인스턴스가 존재하지 않습니다.')
        return instance
    
    @classmethod
    def get_instance(cls, **filter_conditions):
        instance = db.session.query(cls).filter_by(**filter_conditions).first()
        if not instance:
            error_msg('해당하는 인스턴스가 존재하지 않습니다.')
        return instance
    
    @classmethod
    def get_instance_with(cls, *relationships, **filter_conditions):
        options = [selectinload(getattr(cls, attr)) for attr in relationships]
        instance =  db.session.query(cls).filter_by(**filter_conditions).options(*options).first()
        if not instance:
            error_msg('해당하는 인스턴스가 존재하지 않습니다.')
        return instance

    @classmethod
    def count(cls, **filter_conditions):
        return db.session.query(func.count(cls.id)).filter_by(**filter_conditions).scalar()
    
    @classmethod
    def count_all(cls):
        return db.session.query(func.count(cls.id)).scalar()
    
    @classmethod
    def get_all(cls):
        return db.session.query(cls).all() 
    
    @classmethod
    def get_all_with(cls, *relationships, **filter_conditions):
        options = [selectinload(getattr(cls, attr)) for attr in relationships]
        return db.session.query(cls).filter_by(**filter_conditions).options(*options).all() 

    @classmethod
    def is_in_model(cls, **filter_conditions):
        '''
        존재하면 True, X면 False 반환
        '''
        return db.session.query(cls).filter_by(**filter_conditions).scalar() is not None

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
        instances = db.session.query(cls).filter(or_(*conditions)).all()

        duplicate_fields = set()
        for instance in instances:
            for key, value in kwargs.items():
                if getattr(instance, key) == value:
                    duplicate_fields.add(key)

        if duplicate_fields:
            error_msg('중복된 정보가 존재합니다: {}'.format(', '.join(duplicate_fields)))
            return True
        return False

    def add_instance(self):
        db.session.add(self)
        db.session.commit()

    def save_instance(self, **kwargs):
        for key, value in kwargs.items():
            if key in self.__table__.columns:
                setattr(self, key, value)
        db.session.commit()

    def delete_instance(self):
        db.session.delete(self)
        db.session.commit()

    def update_instance(self):
        none_fields = [field for field in self.__class__.__table__.columns if getattr(self, field.name) is None]
        for field in none_fields:
            setattr(self, field.name, field.default.arg)
        db.session.commit()
    
    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
    
    def copy(self):
        new_item = self.__class__()
        for column in self.__table__.columns:
            setattr(new_item, column.name, getattr(self, column.name))
        return new_item

    def __repr__(self):
        return f'{self.__class__.__name__} {self.id}: '

# flask-login 사용하기 위해 UserMixin 상속
class User(BaseModel, UserMixin):
    __tablename__ = 'user'                                                          
    username = db.Column(db.String(150), unique=True)                               # username unique
    email = db.Column(db.String(150), unique=True)                                  # email unique
    password = db.Column(db.String(150))                                            # password 
    date_created = db.Column(db.DateTime, default=datetime.now(KST_offset))         # 회원가입 날짜, 시간 기록
    create_permission = db.Column(db.Boolean, default=False)                        # 글 작성 권한 여부
    admin_check = db.Column(db.Boolean, default=False)                              # 관리자 권한 여부
    auth_type = db.Column(db.Integer, default=0)                                    # 가입 type (0, 1, 2) = (홈페이지, 구글, 카카오)

    posts_count = db.Column(db.Integer, default=0)
    comments_count = db.Column(db.Integer, default=0)
    user_posts = db.relationship('Post', back_populates='user', cascade='delete, delete-orphan', lazy='dynamic')             
    user_comments = db.relationship('Comment', back_populates="user", cascade='delete, delete-orphan', lazy='dynamic') 
    user_messages = db.relationship('Message', back_populates='user', cascade='delete, delete-orphan', lazy='dynamic')     

    def __init__(self, password, **kwargs):
        self.password = generate_password_hash(password)
        super().__init__(**kwargs)
    
    @classmethod
    def user_check(cls, email, password):
        email = email.strip().replace(' ', '')
        user = db.session.query(cls).filter_by(email=email).first()
        if user:
            if not check_password_hash(password, user.password): return user
            else: return error_msg('비밀번호가 틀렸습니다.')
        else: return error_msg('가입되지 않은 이메일입니다.')
    
    def have_create_permission(self):
        return self.create_permission
    
    def have_admin_check(self):
        return self.admin_check

    def update_instance(self):
        self.posts_count = self.user_posts.count()
        self.comments_count = self.user_comments.count()
        super().update_instance()

    def __repr__(self):
        return super().__repr__() + f'{self.username}'                                 
    
class Post(BaseModel):
    __tablename__ = 'post'                                                                          
    title = db.Column(db.String(150), nullable=False)                                               # 제목
    content = db.Column(db.Text, nullable=False)                                                    # 본문 내용
    date_created = db.Column(db.DateTime, default=datetime.now(KST_offset))                         # 글 작성 시간

    author_id = db.Column(db.Integer, db.ForeignKey('user.id', name='fk_post_user', ondelete='CASCADE'), nullable=False)                
    user = db.relationship('User', back_populates='user_posts')             
        
    category_id = db.Column(db.Integer, db.ForeignKey('category.id', name='fk_post_category', ondelete='CASCADE'), nullable=False)   
    category = db.relationship('Category', back_populates='category_posts')    

    comments_count = db.Column(db.Integer, default=0)
    post_comments = db.relationship('Comment', back_populates='post', cascade='delete, delete-orphan', lazy='dynamic')

    def __repr__(self):
        return super().__repr__() + f'{self.title}'   

class Category(BaseModel):
    __tablename__ = 'category'                                                                      # 테이블 이름 명시적 선언
    name = db.Column(db.String(150), unique=True)                                                   # 메뉴 이름       
    category_posts = db.relationship('Post', back_populates='category', cascade='delete, delete-orphan', lazy='dynamic')             

    def __repr__(self):
        return super().__repr__() + f'{self.name}'   

class Comment(BaseModel):
    __tablename__ = 'comment'
    content = db.Column(db.Text(), nullable=False)                                                  # 댓글 내용
    date_created = db.Column(db.DateTime(timezone=True), default=datetime.now(KST_offset))          # 댓글 생성 시간

    author_id = db.Column(db.Integer, db.ForeignKey('user.id', name='fk_comment_user', ondelete='CASCADE'), nullable=False)  
    user = db.relationship('User', back_populates="user_comments")

    post_id = db.Column(db.Integer, db.ForeignKey('post.id', name='fk_comment_post', ondelete='CASCADE'), nullable=False)  
    post = db.relationship('Post', back_populates='post_comments')
    
    def __repr__(self):
        return super().__repr__() + f'{self.post_id} \n{self.content}'

class Message(BaseModel):
    __tablename__ = 'message'
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', name='fk_message_user', ondelete='CASCADE'), nullable=False)
    user = db.relationship('User', back_populates='user_messages')

    def __repr__(self):
        return super().__repr__() + f'user {self.user_id}\'s message \n{self.content}'

def get_model(arg):
    models = {
        'user': User,
        'post': Post,
        'category': Category,
        'comment': Comment,
        'message': Message,
    }
    return models[arg]

from sqlalchemy.event import listens_for
from sqlalchemy.orm import object_session
@listens_for(db.session, 'before_flush')
def after_insert_and_delete(session, flush_context, instances):
    for obj in session.new | session.deleted:
        if isinstance(obj, get_model('comment')):
            if obj.post_id in [x.id for x in session.deleted if isinstance(x, get_model('post'))]:
                # post 삭제 -> comment 삭제인 경우
                user = get_model('user').get_instance(id=obj.author_id)
                post_user_comments_count = object_session(obj).query(func.count(get_model('comment').id)).filter_by(author_id=obj.author_id, post_id=obj.post_id).scalar()
                user.comments_count -= post_user_comments_count
            else:
                post = get_model('post').get_instance(id=obj.post_id)
                post.comments_count = object_session(obj).query(func.count(get_model('comment').id)).filter_by(post_id=obj.post_id).scalar()
                user = get_model('user').get_instance(id=obj.author_id)
                user.comments_count = object_session(obj).query(func.count(get_model('comment').id)).filter_by(author_id=obj.author_id).scalar()
                if obj in session.new:      # 추가
                    post.comments_count += 1
                    user.comments_count += 1
                else:                       # 삭제
                    post.comments_count -= 1
                    user.comments_count -= 1

        elif isinstance(obj, get_model('post')):
            user = user = get_model('user').get_instance(id=obj.author_id)
            user.posts_count = object_session(obj).query(func.count(get_model('post').id)).filter_by(author_id=obj.author_id).scalar()
            if obj in session.new:      # 추가
                user.posts_count += 1
            else:                       # 삭제
                user.posts_count -= 1