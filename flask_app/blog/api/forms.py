from flask_login import current_user
from flask_wtf import FlaskForm
from wtforms import SelectField, StringField, EmailField, PasswordField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, EqualTo

from .utils.etc import Msg
from .models import get_model

class BaseForm(FlaskForm):
    def set_form(self, **kwargs):
        for key, value in kwargs.items():
            self[key].data = value
    
    def set_form_from_obj(self, obj):
        for field_name, value in self._fields.items():
            if hasattr(obj, field_name):
                setattr(value, 'data', getattr(obj, field_name))
    
    def invalid(self):
        if not self.validate_on_submit():
            Msg.error_msg('유효성 검사 실패.')
            return True
        
    def valid(self):
        return self.validate_on_submit()

class SignUpForm(BaseForm):
    username = StringField('username', validators=[DataRequired('사용자 이름은 필수로 입력해야 합니다.'), Length(3,30, '사용자 이름은 3글자 이상 30글자 이하여야 합니다.')])                                
    email = EmailField('email', validators=[DataRequired('사용자 이메일은 필수로 입력해야 합니다.'), Email('이메일 형식을 지켜주세요.')])                        
    password = PasswordField('password', validators=[DataRequired('비밀번호를 입력해주세요.'), Length(6, 30, '비밀번호 길이는 6글자 이상 30글자 이하여야 합니다.')])
    password_check = PasswordField('password_check', validators=[DataRequired(), EqualTo("password", message="비밀번호가 일치해야 합니다.")])
    
class LoginForm(BaseForm):
    email = SignUpForm.email
    password = SignUpForm.password

class PostForm(BaseForm):
    title = StringField('title', validators=[DataRequired('제목을 작성해주세요.')])
    author = StringField('author', render_kw={'readonly': True})
    category_id = SelectField('category', coerce=int, validators=[DataRequired('카테고리를 지정해주세요.')])
    content = TextAreaField('content', validators=[DataRequired('본문을 작성해주세요.')])

    def __init__(self, *args, **kwargs): # 선택 항목 추가
        super(PostForm, self).__init__(*args, **kwargs)
        self.category_id.choices = [(category.id, category.name) for category in get_model('category').get_all()]
        self.author.data = current_user.username

class CommentForm(BaseForm):
    content = TextAreaField('content', validators=[DataRequired('댓글을 작성해주세요.')])

class ContactForm(BaseForm):
    name = StringField('name', render_kw={'readonly': True})
    email = EmailField('email', render_kw={'readonly': True})
    content = TextAreaField('content', validators=[DataRequired('내용을 입력해주세요.')])

    def __init__(self, *args, **kwargs):
        super(ContactForm, self).__init__(*args, **kwargs)
        self.name.data = current_user.username
        self.email.data = current_user.email

class OtpForm(BaseForm):
    otp = StringField('otp', validators=[Length(6, 6, 'OTP는 6글자여야 합니다.')])

class CategoryForm(BaseForm):
    name = StringField('category', validators=[Length(3, 20, '카테고리는 3자 이상 20자 이하여야 합니다.')])

class UserInfoForm(BaseForm):
    username = SignUpForm.username