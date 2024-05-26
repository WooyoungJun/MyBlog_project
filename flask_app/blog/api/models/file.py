from os.path import splitext
from datetime import datetime

from blog.api.utils.etc import Etc
from blog.api.models import get_db
from blog.api.models.base import BaseModel

db = get_db()

class File(BaseModel):
    __tablename__ = 'file'
    name = db.Column(db.String(150), nullable=False)
    size = db.Column(db.Float, nullable=False)

    author_id = db.Column(db.Integer, db.ForeignKey('user.id', name='fk_file_user', ondelete='CASCADE'), nullable=False)                
    user = db.relationship('User', back_populates='files')             
    
    post_id = db.Column(db.Integer, db.ForeignKey('post.id', name='fk_file_post', ondelete='CASCADE'), nullable=False)
    post = db.relationship('Post', back_populates='files')

    @staticmethod
    def get_s3_config():
        config = Etc.get_config()
        return config['S3'], config['S3_BUCKET_NAME'], config['S3_DEFAULT_DIRS'][config['mode']]

    @classmethod
    def make_new_file_name(cls, filename, s3_default_dir):
        origin_file_name, extension = splitext(filename)
        origin_file_name = origin_file_name.replace(' ', '_')
        now = str(int(datetime.now().timestamp()*100000))
        new_file_name = origin_file_name + '_' + now + extension
        if len(new_file_name) + len(s3_default_dir) > 150: 
            # 길이 제한 150자
            new_file_name = new_file_name[-150 + len(s3_default_dir)]
        return new_file_name
    
    @classmethod
    def upload_to_s3(cls, file, post_id, author_id):
        '''
        file 인스턴스 추가 + s3에 업로드
        '''
        s3, s3_bucket_name, s3_default_dir = cls.get_s3_config()

        new_file_name = cls.make_new_file_name(file.filename, s3_default_dir)
        file_size = file.getbuffer().nbytes
        
        cls(
            name=new_file_name,
            size=file_size,
            post_id=post_id,
            author_id=author_id,
        ).add_instance()
        
        s3.upload_fileobj(file, s3_bucket_name, s3_default_dir + new_file_name)
        file.close()
        return file_size

    def before_deleted_flush(self):
        s3, s3_bucket_name, s3_default_dir = self.get_s3_config()

        try:
            s3.delete_object(Bucket=s3_bucket_name, Key=s3_default_dir + self.name)
        except Exception as e:
            print('에러가 발생했습니다: ', str(e))

    def __repr__(self):
        return super().__repr__() + f'{self.name}'         

    def __str__(self):
        return super().__str__() + f'{self.name}'

# ------------------------------------------ Admin ------------------------------------------   
from blog.api.models.base import AdminBase

class FileAdmin(AdminBase):
    # 1. 표시 할 열 설정
    column_list = ('id', 'name', 'size', 'post_id')

    # 2. 폼 표시 X 열 설정
    form_excluded_columns = {'post'} 