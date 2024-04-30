from flask import Blueprint, jsonify, url_for, redirect
from flask_login import current_user

from .forms import CommentForm, ContactForm, PostForm
from .models import get_model
from .utils import (
    only_delete_method, only_post_method, 
    render_template_with_user, create_permission_required,          # 데코레이터 함수

    get_method, post_method, form_invalid, form_valid, 
    success_msg, is_owner, error                                    # 기타
)

views = Blueprint('views', __name__)
BASE_VIEWS_DIR = 'views/'

def render_template_views(template_name_or_list, **context):
    context['template_name_or_list'] = BASE_VIEWS_DIR + template_name_or_list
    return render_template_with_user(**context)

# ------------------------------------------------------------ posts_list 출력 페이지 ------------------------------------------------------------
@views.route('/')
@views.route('/home')
def home():
    # 쿼리 최대 4번 = posts 3번 + user 1번
    posts = get_model('post').get_all_with('user', 'category')
    return render_template_views(
        'posts_list.html', 
        posts=posts, 
        type='home',
        category_name='all',
    )

@views.route('/user_posts/<int:user_id>')
def user_posts(user_id):
    # 쿼리 최대 4번 = selected_user 1번 + user_posts 2번 + user 1번
    selected_user = get_model('user').get_instance_by_id(user_id)
    if not selected_user: return error(404)

    user_posts = get_model('post').get_all_with('category', author_id=user_id)
    return render_template_views(
        'posts_list.html', 
        posts=user_posts, 
        type='user_posts',
        selected_user=selected_user,
    )

@views.route('/category')
def category():
    # 쿼리 최대 2번 = category 1번 + user 1번
    categories = get_model('category').get_all()
    return render_template_views(
        'category.html', 
        categories=categories,
    )

@views.route('/posts-list/<int:category_id>')
def posts_list(category_id):
    # 쿼리 최대 4번 = selected_category 1번 + category_posts 2번 + user 1번
    selected_category = get_model('category').get_instance_by_id(category_id)
    if not selected_category: return error(404)

    category_posts = get_model('post').get_all_with('user', 'category', category_id=category_id)
    return render_template_views(
        'posts_list.html', 
        posts=category_posts, 
        type='category_posts',
        category_name=selected_category.name,
    )

# ------------------------------------------------------------ about-me & contact 페이지 ------------------------------------------------------------
@views.route('/about-me')
def about_me():
    return render_template_views('about_me.html')
    
@views.route('/contact', methods=['GET', 'POST'])
@create_permission_required
def contact():
    form = ContactForm()

    if post_method() and form_valid(form):
        get_model('message')(
            content=form.content.data,
            user_id=current_user.id,
        ).add_instance()
        success_msg('메세지 전송이 완료되었습니다.')
        form.content.data = ''

    return render_template_views('contact.html', form=form)
    
# ------------------------------------------------------------ post 관련 페이지 ------------------------------------------------------------
@views.route('/post/<int:post_id>')
def post(post_id):
    form = CommentForm()

    # 쿼리 최대 6번 = post 3번 + post_comments 2번 + user 1번
    post = get_model('post').get_instance_by_id_with(post_id, 'user', 'category')
    if not post: return error(404)
    
    post_comments = get_model('comment').get_all_with('user', post_id=post_id)
    return render_template_views(
        'post_read.html', 
        post=post,
        form=form,
        comments=post_comments,
    )

@views.route('/post-create', methods=['GET', 'POST'])
@create_permission_required
def post_create():
    form = PostForm()

    # GET 요청 = 쿼리 최대 2번 = user 1번 + category 1번  
    # POST 요청 = 쿼리 최대 3번 = user 1번 + category 1번 + post 추가(user_posts 업데이트) 1번
    # home 돌아옴 = 쿼리 최대 4번 = posts 3번 + user 1번
    if get_method() or form_invalid(form):
        return render_template_views(
            'post_write.html', 
            form=form, 
            type='Create',
        )
    
    get_model('post')(
        title=form.title.data,
        content=form.content.data,
        category_id=form.category_id.data,
        author_id=current_user.id,
    ).add_instance()
    success_msg('Post 작성 완료!')
    return redirect(url_for('views.home'))

@views.route('/post-edit/<int:post_id>', methods=['GET', 'POST'])
@create_permission_required
def post_edit(post_id):
    form = PostForm()
    params = {
        'form':form, 
        'type':'Edit',
        'post_id':post_id,
    }

    # GET 요청 = 쿼리 최대 3번 = user 1번 + post 1번 + category 1번
    # POST 요청 = 쿼리 최대 3번 = user 1번 + category 1번 + post 추가(user_posts 업데이트) 1번
    # post 읽기 돌아옴 = 쿼리 최대 6번 = post 3번 + post_comments 2번 + user 1번
    post = get_model('post').get_instance_by_id(post_id)
    if not post: return error(404)
    if not is_owner(post.author_id): return error(403)

    if get_method():
        form.set_form_from_obj(post)
        return render_template_views('post_write.html', **params)
    
    if form_invalid(form): return render_template_views('post_write.html', **params)
    
    post.save_instance(
        title=form.title.data, 
        content=form.content.data, 
        category_id=form.category_id.data
    )
    success_msg('Post 수정 완료!')
    return redirect(url_for('views.post', post_id=post_id))

@views.route('/post-delete/<int:post_id>', methods=['DELETE'])
@only_delete_method
@create_permission_required
def post_delete(post_id):
    # 쿼리 최대 4번 = user 1번 + post 삭제 1번 + user의 posts_count update 1번 + comments 삭제 1번
    # + comments 관련 user update N번
    # home 돌아옴 = 쿼리 최대 4번 = posts 3번 + user 1번
    post = get_model('post').get_instance_by_id(post_id)
    if not post: return jsonify(message='error'), 404
    if not is_owner(post.author_id): return error(403)

    post.delete_instance()
    success_msg('게시물이 성공적으로 삭제되었습니다.')
    return jsonify(message='success'), 200

# ------------------------------------------------------------ comment 관련 기능들 ------------------------------------------------------------
@views.route('/comment-create/<int:post_id>', methods=['POST'])
@only_post_method
@create_permission_required
def comment_create(post_id): 
    form = CommentForm()

    # POST 요청 = 쿼리 최대 4번 = user 1번 + comment 추가(post조회 + post_comments + user_comments update 3번)
    # post 읽기 돌아옴 = 쿼리 최대 6번 = post 3번 + post_comments 2번 + user 1번
    if form_invalid(form): return redirect(url_for('views.post', post_id=post_id))
    
    get_model('comment')(
        content=form.content.data,
        author_id=current_user.id,
        post_id=post_id
    ).add_instance()
    success_msg('댓글 작성 성공!')
    return redirect(url_for('views.post', post_id=post_id))

@views.route('/comment-edit/<int:comment_id>', methods=['POST'])
@only_post_method
@create_permission_required
def comment_edit(comment_id):
    form = CommentForm()
    
    # POST 요청 = 쿼리 최대 4번 = user 1번 + comment update 1번
    # post 읽기 돌아옴 = 쿼리 최대 6번 = post 3번 + post_comments 2번 + user 1번
    comment = get_model('comment').get_instance_by_id(comment_id)
    if not comment: return error(404)
    if not is_owner(comment.author_id): return error(403)

    if form_valid(form):
        comment.save_instance(content=form.content.data)
        success_msg('댓글 수정 완료!')

    return redirect(url_for('views.post', post_id=comment.post_id))
    

@views.route('/comment-delete/<int:comment_id>', methods=['DELETE'])
@only_delete_method
@create_permission_required
def comment_delete(comment_id):
    # POST 요청 = 쿼리 최대 5번 = user 1번 + comment, post 로드 2번 + comment 관련 업데이트(post + user) 2번 
    # post 읽기 돌아옴 = 쿼리 최대 6번 = post 3번 + post_comments 2번 + user 1번
    comment = get_model('comment').get_instance_by_id(comment_id)
    if not comment: return jsonify(message='error'), 404
    if not is_owner(comment.author_id): return error(403)

    comment.delete_instance()
    success_msg('댓글이 성공적으로 삭제되었습니다.')
    return jsonify(message='success'), 200