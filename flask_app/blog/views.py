from flask import Blueprint, abort, flash, jsonify, url_for, redirect, render_template, request
from flask_login import current_user
from blog.forms import CommentForm, ContactForm, PostForm
from blog.models import get_model
from .utils import create_permission_required, instance_check, is_owner, only_post_method

views = Blueprint('views', __name__)
BASE_VIEWS_DIR = 'views/'

# ------------------------------------------------------------ posts_list 출력 페이지 ------------------------------------------------------------
@views.route("/")
@views.route("/home")
def home():
    # 쿼리 최대 4번 = posts 3번 + user 1번
    posts = get_model('post').get_all('user', 'category')
    
    return render_template(BASE_VIEWS_DIR + "posts_list.html", 
        user=current_user, 
        posts=posts, 
        type='home',
        category_name='all',
    )

@views.route('/category')
def category():
    # 쿼리 최대 2번 = category 1번 + user 1번
    categories = get_model('category').get_all()

    return render_template(BASE_VIEWS_DIR + "category.html", 
        user=current_user, 
        categories=categories,
    )

@views.route("/posts-list/<int:category_id>")
def posts_list(category_id):
    # 쿼리 최대 4번 = selected_category 1번 + category_posts 2번 + user 1번
    selected_category = get_model('category').get_instance(id=category_id)
    category_posts = get_model('post').get_all('user', 'category', category_id=category_id)

    if instance_check(category_posts, '카테고리'): return redirect(url_for('views.category'))
    
    return render_template(BASE_VIEWS_DIR + "posts_list.html", 
        user=current_user, 
        posts=category_posts, 
        type='category_posts',
        category_name=selected_category.name,
    )

@views.route("/user_posts/<int:user_id>")
def user_posts(user_id):
    # 쿼리 최대 4번 = selected_user 1번 + user_posts 2번 + user 1번
    selected_user = get_model('user').get_instance(id=user_id)
    user_posts = get_model('post').get_all('category', author_id=user_id)

    if instance_check(user_posts, '유저의 post'): return redirect(url_for('views.home'))
    
    return render_template(BASE_VIEWS_DIR + "posts_list.html", 
        user=current_user, 
        posts=user_posts, 
        type='user_posts',
        selected_user=selected_user,
    )

# ------------------------------------------------------------ about-me & contact 출력 페이지 ------------------------------------------------------------
@views.route("/about-me")
def about_me():
    return render_template(BASE_VIEWS_DIR + "about_me.html", user=current_user)
    
@views.route("/contact", methods=['GET', 'POST'])
@create_permission_required
def contact():
    form = ContactForm()

    if request.method == 'POST' and form.validate_on_submit():
        get_model('message')(
            content=form.content.data,
            user_id=current_user.id,
        ).add_instance()
        flash('메세지 전송이 완료되었습니다.', category="success")
        form.content.data = ''

    return render_template(BASE_VIEWS_DIR + "contact.html", 
        user=current_user,
        form=form,
    )
    
# ------------------------------------------------------------ post 관련 페이지 ------------------------------------------------------------
@views.route('/post/<int:post_id>')
def post(post_id):
    form = CommentForm()

    # 쿼리 최대 6번 = post 3번 + post_comments 2번 + user 1번
    post = get_model('post').get_instance('user', 'category', id=post_id)

    if instance_check(post, 'post'): return redirect(url_for('views.home'))
    
    post_comments = get_model('comment').get_all('user', post_id=post_id)

    return render_template(BASE_VIEWS_DIR + "post_read.html", 
        user=current_user, 
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
    if request.method == 'GET' or not form.validate_on_submit():
        return render_template(BASE_VIEWS_DIR + "post_write.html", 
            user=current_user, 
            form=form, 
            type='Create',
        )
    
    get_model('post')(
        title=form.title.data,
        content=form.content.data,
        category_id=form.category_id.data,
        author_id=current_user.id,
    ).add_instance()
    flash('Post 작성 완료!', category="success")
    return redirect(url_for('views.home'))

@views.route('/post-edit/<int:post_id>', methods=['GET', 'POST'])
@create_permission_required
def post_edit(post_id):
    form = PostForm()
    params = {
        'user':current_user, 
        'form':form, 
        'type':"Edit",
        'post_id':post_id,
    }

    # GET 요청 = 쿼리 최대 3번 = user 1번 + post 1번 + category 1번
    # POST 요청 = 쿼리 최대 3번 = user 1번 + category 1번 + post 추가(user_posts 업데이트) 1번
    # post 읽기 돌아옴 = 쿼리 최대 6번 = post 3번 + post_comments 2번 + user 1번
    post = get_model('post').get_instance(id=post_id)

    if instance_check(post, 'post'): return redirect(url_for('views.home'))
    
    if not is_owner(post.author_id): return abort(403)

    if request.method == 'GET':
        form.set_form(post)
        return render_template(BASE_VIEWS_DIR + "post_write.html", **params)
    
    if not form.validate_on_submit():
        flash('Post 수정 실패!', category="error")
        return render_template(BASE_VIEWS_DIR + "post_write.html", **params)
    
    post.save_instance(
        title=form.title.data, 
        content=form.content.data, 
        category_id=form.category_id.data
    )
    flash('Post 수정 완료!', category="success")
    return redirect(url_for('views.post', post_id=post_id))

@views.route('/post-delete/<int:post_id>', methods=['POST'])
@only_post_method
@create_permission_required
def post_delete(post_id):
    # 쿼리 최대 4번 = user 1번 + post 삭제 1번 + user의 posts_count update 1번 + comments 삭제 1번
    # + comments 관련 user update N번
    # home 돌아옴 = 쿼리 최대 4번 = posts 3번 + user 1번
    post = get_model('post').get_instance(id=post_id)

    if instance_check(post, 'post'): return jsonify(message='error'), 400
    
    if not is_owner(post.author_id): return abort(403)

    post.delete_instance()
    flash('게시물이 성공적으로 삭제되었습니다.', 'success')
    return jsonify(message='success'), 200

# ------------------------------------------------------------ comment 관련 기능들 ------------------------------------------------------------
@views.route('/comment-create/<int:post_id>', methods=['POST'])
@only_post_method
@create_permission_required
def comment_create(post_id): 
    form = CommentForm()

    # POST 요청 = 쿼리 최대 4번 = user 1번 + comment 추가(post조회 + post_comments + user_comments update 3번)
    # post 읽기 돌아옴 = 쿼리 최대 6번 = post 3번 + post_comments 2번 + user 1번
    if not form.validate_on_submit():
        flash('댓글 작성 실패!', category="error")
        return redirect(url_for('views.post', post_id=post_id))
    
    get_model('comment')(
        content=form.content.data,
        author_id=current_user.id,
        post_id=post_id
    ).add_instance()
    flash('댓글 작성 성공!', category="success")
    return redirect(url_for('views.post', post_id=post_id))

@views.route('/comment-edit/<int:comment_id>', methods=['POST'])
@only_post_method
@create_permission_required
def comment_edit(comment_id):
    form = CommentForm()
    
    # POST 요청 = 쿼리 최대 4번 = user 1번 + comment update 1번
    # post 읽기 돌아옴 = 쿼리 최대 6번 = post 3번 + post_comments 2번 + user 1번
    
    comment = get_model('comment').get_instance(id=comment_id)

    if instance_check(comment, 'comment'): return redirect(url_for('views.home'))
    
    if not is_owner(comment.author_id): return abort(403)

    if not form.validate_on_submit():
        flash('댓글 수정 실패!', category="error")
    else:
        comment.save_instance(content=form.content.data)
        flash('댓글 수정 완료!', category="success")

    return redirect(url_for('views.post', post_id=comment.post_id))
    

@views.route('/comment-delete/<int:comment_id>', methods=['POST'])
@only_post_method
@create_permission_required
def comment_delete(comment_id):
    # POST 요청 = 쿼리 최대 5번 = user 1번 + comment, post 로드 2번 + comment 관련 업데이트(post + user) 2번 
    # post 읽기 돌아옴 = 쿼리 최대 6번 = post 3번 + post_comments 2번 + user 1번
    comment = get_model('comment').get_instance(id=comment_id)

    if instance_check(comment, 'comment'): return jsonify(message='error'), 400
    
    if not is_owner(comment.author_id): return abort(403)

    comment.delete_instance()
    flash('댓글이 성공적으로 삭제되었습니다.', 'success')
    return jsonify(message='success'), 200