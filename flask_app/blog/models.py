from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from flask_migrate import Migrate
from datetime import datetime, timedelta, timezone
from werkzeug.security import generate_password_hash

# 한국 시간대 오프셋(UTC+9)을 생성합니다.
KST_offset = timezone(timedelta(hours=9))

db = SQLAlchemy()
migrate = Migrate()

# relationship(관계 맺는 모델 이름, backref=(관계 맺는 해당 모델 속성 명, 한 객체 변경시 적용할 속성))
# all = 모두
# save-update = session에 변경 add 시, 연결된 모든 객체도 session에 add
# delete = 삭제될 때만
# delete-orphan = delete + 관계가 끊길 때도 추가 삭제
# lazy='selectin': 주 객체를 가져오는 쿼리에 관련된 모든 객체를 가져오는 서브쿼리를 사용하여 즉시 로드
# 실제 사용할 때는 sqlalchemy.orm.selectinload 메소드 사용 = N+1 문제 해결

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

    def __init__(self, username, email, password, post_create_permission=False, admin_check=False):
        self.username = username
        self.email = email
        self.password = generate_password_hash(password)
        self.date_created = datetime.now(KST_offset)                                      
        self.post_create_permission = post_create_permission 
        self.admin_check = admin_check

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

    user = db.relationship('User', backref=db.backref('user_posts', cascade='delete, delete-orphan', lazy='selectin'))    
    category = db.relationship('Category', backref=db.backref('category_posts', cascade='delete, delete-orphan', lazy='selectin')) 

    def __init__(self, author_id, title='', content='', category_id=1):
        self.title = title
        self.content = content
        self.date_created = datetime.now(KST_offset)
        self.author_id = author_id
        self.category_id = category_id

    def __repr__(self):
        return f'{self.__class__.__name__} {self.id}: {self.title}'

class Category(db.Model):
    __tablename__ = 'category'                                                                      # 테이블 이름 명시적 선언
    id = db.Column(db.Integer, primary_key=True)                                                    # 메뉴 고유 번호
    name = db.Column(db.String(150), unique=True)                                                   # 메뉴 이름                    

    def __repr__(self):
        return f'{self.__class__.__name__} {self.id}: {self.name}'

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)                                                    # 댓글 고유 번호
    content = db.Column(db.Text(), nullable=False)                                                  # 댓글 내용
    date_created = db.Column(db.DateTime(timezone=True), default=datetime.now(KST_offset))            # 댓글 생성 시간

    author_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)  
    post_id = db.Column(db.Integer, db.ForeignKey('post.id', ondelete='CASCADE'), nullable=False)  

    user = db.relationship('User', backref=db.backref('user_comments', cascade='delete, delete-orphan'), lazy='selectin')
    post = db.relationship('Post', backref=db.backref('post_comments', cascade='delete, delete-orphan'), lazy='selectin')

    def __repr__(self):
        return f'{self.__class__.__name__}(title={self.content})>'
    
def get_model(arg):
    models = {
        'user': User,
        'post': Post,
        'category': Category,
        'comment': Comment,
    }
    return models[arg]