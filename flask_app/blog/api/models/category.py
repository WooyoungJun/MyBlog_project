from blog.api.models.base import BaseModel
from blog.api.models import get_db

db = get_db()

class Category(BaseModel):
    __tablename__ = 'category'                                                                      # 테이블 이름 명시적 선언
    name = db.Column(db.String(150), unique=True)                                                   # 메뉴 이름       
    category_posts = db.relationship('Post', back_populates='category', cascade='delete, delete-orphan', lazy='dynamic')             

    def __repr__(self):
        return super().__repr__() + f'{self.name}'         

    def __str__(self):
        return super().__str__() + f'{self.name}'

# ------------------------------------------ Admin ------------------------------------------   
from blog.api.models.base import AdminBase

class CategoryAdmin(AdminBase):
    # 1. 표시 할 열 설정
    column_list = ('id', 'name')

    # 2. 폼 표시 X 열 설정
    form_excluded_columns = {'category_posts'} 