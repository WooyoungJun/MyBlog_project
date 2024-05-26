from sqlalchemy import String, or_, func
from sqlalchemy.orm import selectinload, joinedload
from json import dumps

from blog.api.utils.etc import Msg, Etc

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

from blog.api.models import get_db
db = get_db()

class BaseModel(db.Model):
    __abstract__ = True                                                             # 추상 클래스 설정
    id = db.Column(db.Integer, primary_key=True)                                    # primary key 설정
    date_created = db.Column(db.DateTime, default=Etc.get_korea_time())
        
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

from sqlalchemy.event import listens_for
@listens_for(db.session, 'before_flush')
def before_flush(session, flush_context, instances):
    for obj in session.deleted:
        if hasattr(obj, 'before_deleted_flush'):
            obj.before_deleted_flush()
    
    for obj in session.new:
        if hasattr(obj, 'before_new_flush'):
            obj.before_new_flush()

# ------------------------------------------ Admin ------------------------------------------
from flask_admin import AdminIndexView, expose
from flask_login import current_user
from flask_admin.contrib.sqla import ModelView

from blog.api.utils.error import Error

class CustomAdminIndexView(AdminIndexView):
    def is_accessible(self):
        if current_user.is_authenticated == True and current_user.admin_check == True:
            return True
        else:
            return Error.error(403)
        
    @expose('/')
    def index(self):
        return self.render('admin/admin_base.html', username=current_user.username)
    
class AdminBase(ModelView):
    column_formatters = {
        'date_created': lambda view, context, model, name: model.date_created.strftime('%Y-%m-%d %H:%M:%S')
    }
    
    def is_accessible(self):
        if current_user.is_authenticated == True and current_user.admin_check == True:
            return True
        else:
            return Error.error(403)
        
    # 사용자 지정 도구 추가
    from flask_admin.actions import action
    @action('update_model_instances', 'Update Model', 'Are you sure you want to update model for selected object?')
    def update_model_instances(self, ids):
        instances = self.model.get_all_by_ids(ids)
        for instance in instances:
            instance.fill_none_fields()
            if hasattr(instance, 'update_count'):
                instance.update_count()
        self.model.commit()