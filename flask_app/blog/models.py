from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event, func
from sqlalchemy.orm import object_session
from flask_login import UserMixin
from flask_migrate import Migrate
from datetime import datetime, timedelta, timezone
from werkzeug.security import generate_password_hash

# 한국 시간대 오프셋(UTC+9)을 생성합니다.
KST_offset = timezone(timedelta(hours=9))

db = SQLAlchemy()
migrate = Migrate()

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


# flask-login 사용하기 위해 UserMixin 상속
class User(db.Model, UserMixin):
    __tablename__ = 'user'                                                          # 테이블 이름 명시적 선언
    id = db.Column(db.Integer, primary_key=True)                                    # primary key 설정
    username = db.Column(db.String(150), unique=True)                               # username unique
    email = db.Column(db.String(150), unique=True)                                  # email unique
    password = db.Column(db.String(150))                                            # password 
    date_created = db.Column(db.DateTime, default=datetime.now(KST_offset))         # 회원가입 날짜, 시간 기록
    post_create_permission = db.Column(db.Boolean, default=False)                   # 글 작성 권한 여부
    admin_check = db.Column(db.Boolean, default=False)                              # 관리자 권한 여부

    posts_count = db.Column(db.Integer, default=0)
    comments_count = db.Column(db.Integer, default=0)
    user_posts = db.relationship('Post', back_populates='user', cascade='delete, delete-orphan', lazy='dynamic')             
    user_comments = db.relationship('Comment', back_populates="user", cascade='delete, delete-orphan', lazy='dynamic') 
    user_messages = db.relationship('Message', back_populates='user', cascade='delete, delete-orphan', lazy='dynamic')     

    def __init__(self, username, email, password, post_create_permission=False, admin_check=False, posts_count=0, comments_count=0):
        self.username = username
        self.email = email
        self.password = generate_password_hash(password)
        self.date_created = datetime.now(KST_offset)                                      
        self.post_create_permission = post_create_permission 
        self.admin_check = admin_check
        self.posts_count = posts_count
        self.comments_count = comments_count

    def update_myinfo(self):
        self.posts_count = self.user_posts.count()
        self.comments_count = self.user_comments.count()
        db.session.commit()

    def __repr__(self):
        return f'{self.__class__.__name__} {self.id}: {self.username}'                                  
    
class Post(db.Model):
    __tablename__ = 'post'                                                                          # 테이블 이름 명시적 선언
    id = db.Column(db.Integer, primary_key=True)                                                    # 글 고유 번호
    title = db.Column(db.String(150), nullable=False)                                               # 제목
    content = db.Column(db.Text, nullable=False)                                                    # 본문 내용
    date_created = db.Column(db.DateTime, default=datetime.now(KST_offset))                         # 글 작성 시간

    author_id = db.Column(db.Integer, db.ForeignKey('user.id', name='fk_post_user', ondelete='CASCADE'), nullable=False)                
    category_id = db.Column(db.Integer, db.ForeignKey('category.id', name='fk_post_category', ondelete='CASCADE'), nullable=False)   

    user = db.relationship('User', back_populates='user_posts')                 
    category = db.relationship('Category', back_populates='category_posts')    

    comments_count = db.Column(db.Integer, default=0)
    post_comments = db.relationship('Comment', back_populates='post', cascade='delete, delete-orphan', lazy='dynamic')

    def __init__(self, author_id, title='', content='', category_id=1, comments_count=0):
        self.title = title
        self.content = content
        self.date_created = datetime.now(KST_offset)
        self.author_id = author_id
        self.category_id = category_id
        self.comments_count = comments_count

    def __repr__(self):
        return f'{self.__class__.__name__} {self.id}: {self.title}'

class Category(db.Model):
    __tablename__ = 'category'                                                                      # 테이블 이름 명시적 선언
    id = db.Column(db.Integer, primary_key=True)                                                    # 메뉴 고유 번호
    name = db.Column(db.String(150), unique=True)                                                   # 메뉴 이름       

    category_posts = db.relationship('Post', back_populates='category', cascade='delete, delete-orphan', lazy='dynamic')             

    def __repr__(self):
        return f'{self.__class__.__name__} {self.id}: {self.name}'

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)                                                    # 댓글 고유 번호
    content = db.Column(db.Text(), nullable=False)                                                  # 댓글 내용
    date_created = db.Column(db.DateTime(timezone=True), default=datetime.now(KST_offset))          # 댓글 생성 시간

    author_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)  
    post_id = db.Column(db.Integer, db.ForeignKey('post.id', ondelete='CASCADE'), nullable=False)  

    user = db.relationship('User', back_populates="user_comments")
    post = db.relationship('Post', back_populates='post_comments')
    
    def __repr__(self):
        return f'{self.__class__.__name__}(title={self.content})>'

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)

    user = db.relationship('User', back_populates='user_messages')

def get_model(arg):
    models = {
        'user': User,
        'post': Post,
        'category': Category,
        'comment': Comment,
        'message': Message
    }
    return models[arg]

@event.listens_for(db.session, 'before_flush')
def after_insert_and_delete(session, flush_context, instances):
    for obj in session.new | session.deleted:
        if isinstance(obj, get_model('comment')):
            post = db.session.get(get_model('post'), obj.post_id)
            post.comments_count = object_session(obj).query(func.count(get_model('comment').id)).filter_by(post_id=obj.post_id).scalar()

            user = db.session.get(get_model('user'), obj.author_id)
            user.comments_count = object_session(obj).query(func.count(get_model('comment').id)).filter_by(author_id=obj.author_id).scalar()
            if obj in session.new:      # 추가
                post.comments_count += 1
                user.comments_count += 1
            else:                       # 삭제
                post.comments_count -= 1
                user.comments_count -= 1

        elif isinstance(obj, get_model('post')):
            user = db.session.get(get_model('user'), obj.author_id)
            user.posts_count = object_session(obj).query(func.count(get_model('post').id)).filter_by(author_id=obj.author_id).scalar()
            if obj in session.new:      # 추가
                user.posts_count += 1
            else:                       # 삭제
                user.posts_count -= 1