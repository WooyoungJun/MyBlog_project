from flask import Blueprint, abort, flash, jsonify, url_for, redirect, render_template, request
from flask_login import current_user, login_required
from blog.forms import CommentForm, ContactForm, PostForm
from blog.models import db, get_model
from sqlalchemy.orm import selectinload

views = Blueprint('views', __name__)
BASE_VIEWS_DIR = 'views/'

# post = get_model('post').query.get(id) 대신 아래처럼 사용(deprecated)
# post = db.session.get(get_model('post'), id)


# ------------------------------------------------------------ posts_list 출력 페이지 ------------------------------------------------------------
@views.route("/")
@views.route("/home")
def home():
    # 쿼리 최대 4번 = posts 3번 + user 1번
    posts = db.session.query(get_model('post')).options(selectinload(get_model('post').user), selectinload(get_model('post').category)).all() 
    return render_template(BASE_VIEWS_DIR + "posts_list.html", 
        user=current_user, 
        posts=posts, 
        type='home',
        category_name='all',
    )

@views.route('/category')
def category():
    # 쿼리 최대 2번 = category 1번 + user 1번
    categories = db.session.query(get_model('category')).all()
    return render_template(BASE_VIEWS_DIR + "category.html", 
        user=current_user, 
        categories=categories,
    )

@views.route("/posts-list/<int:category_id>")
def posts_list(category_id):
    # 쿼리 최대 4번 = selected_category 1번 + category_posts 2번 + user 1번
    selected_category = db.session.get(get_model('category'), category_id)
    category_posts = db.session.query(get_model('post')).filter_by(category_id=category_id).options(selectinload(get_model('post').user)).all() 
    if category_posts is None:
        flash('해당 카테고리는 존재하지 않습니다.', category="error")
        return redirect(url_for('views.category'))
    
    return render_template(BASE_VIEWS_DIR + "posts_list.html", 
        user=current_user, 
        posts=category_posts, 
        type='category_posts',
        category_name=selected_category.name,
    )

@views.route("/user_posts/<int:user_id>")
def user_posts(user_id):
    # 쿼리 최대 4번 = selected_user 1번 + user_posts 2번 + user 1번
    selected_user = db.session.get(get_model('user'), user_id)
    user_posts = db.session.query(get_model('post')).filter_by(author_id=user_id).options(selectinload(get_model('post').category)).all() 
    if user_posts is None:
        flash('해당 유저가 작성한 글이 존재하지 않습니다.', category="error")
        return redirect(url_for('views.home'))
    
    return render_template(BASE_VIEWS_DIR + "posts_list.html", 
        user=current_user, 
        posts=user_posts, 
        type='user_posts',
        selected_user=selected_user,
    )

# ------------------------------------------------------------ about-me & contact & mypage 출력 페이지 ------------------------------------------------------------
@views.route("/about-me")
def about_me():
    return render_template(BASE_VIEWS_DIR + "about_me.html", 
        user=current_user,
    )
    
@views.route("/contact", methods=['GET', 'POST'])
@login_required
def contact():
    form = ContactForm()

    if request.method == 'POST' and form.validate_on_submit():
        message = get_model('message')(
            content=form.content.data,
            user_id=current_user.id,
        )
        db.session.add(message)
        db.session.commit()
        flash('메세지 전송이 완료되었습니다.', category="success")
        form.content.data = ''

    return render_template(BASE_VIEWS_DIR + "contact.html", 
        user=current_user,
        form=form,
    )

@views.route('/mypage')
@login_required
def mypage():
    return render_template(BASE_VIEWS_DIR + "mypage.html", 
        user=current_user,
    )
    
# ------------------------------------------------------------ post 관련 페이지 ------------------------------------------------------------
@views.route('/post/<int:post_id>')
def post(post_id):
    form = CommentForm()

    # 쿼리 최대 6번 = post 3번 + post_comments 2번 + user 1번
    post = db.session.get(get_model('post'), post_id, options=[selectinload(get_model('post').user), selectinload(get_model('post').category)])
    if post is None:
        flash('해당 포스트는 존재하지 않습니다.', category="error")
        return redirect(url_for('views.home'))
    
    post_comments = db.session.query(get_model('comment')).filter_by(post_id=post_id).options(selectinload(get_model('comment').user)).all()
    
    return render_template(BASE_VIEWS_DIR + "post_read.html", 
        user=current_user, 
        post=post,
        form=form,
        comments=post_comments,
    )

@views.route('/post-create', methods=['GET', 'POST'])
@login_required
def post_create():
    # GET 요청 = 쿼리 최대 2번 = user 1번 + category 1번  
    # POST 요청 = 쿼리 최대 3번 = user 1번 + category 1번 + post 추가(user_posts 업데이트) 1번
    # home 돌아옴 = 쿼리 최대 4번 = posts 3번 + user 1번
    if current_user.post_create_permission == False: return abort(403)

    form = PostForm()
    if request.method == 'POST' and form.validate_on_submit():
        post = get_model('post')(
            title=form.title.data,
            content=form.content.data,
            category_id=form.category_id.data,
            author_id=current_user.id,
        )
        db.session.add(post)
        db.session.commit()
        flash('Post 작성 완료!', category="success")
        return redirect(url_for('views.home'))
    else: # GET 요청 or form invalidated
        return render_template(BASE_VIEWS_DIR + "post_write.html", 
            user=current_user, 
            form=form, 
            type='Create',
        )

@views.route('/post-edit/<int:post_id>', methods=['GET', 'POST'])
@login_required
def post_edit(post_id):
    # GET 요청 = 쿼리 최대 3번 = user 1번 + post 1번 + category 1번
    # POST 요청 = 쿼리 최대 3번 = user 1번 + category 1번 + post 추가(user_posts 업데이트) 1번
    # post 읽기 돌아옴 = 쿼리 최대 6번 = post 3번 + post_comments 2번 + user 1번
    post = db.session.get(get_model('post'), post_id)
    if post is None:
        flash('게시물을 찾을 수 없습니다.', 'error')
        return redirect(url_for('views.home'))
    
    # 작성자가 아니면 abort
    if current_user.id != post.author_id: return abort(403)

    form = PostForm()

    if request.method == 'GET':
        # 기존 post 데이터 채우기
        form.title.data = post.title
        form.content.data = post.content
        form.category_id.data = post.category_id
        return render_template(BASE_VIEWS_DIR + "post_write.html", 
            user=current_user, 
            form=form, 
            type="Edit",
            post_id=post_id,
        )
    
    if request.method == 'POST' and form.validate_on_submit():
        # 새로운 post 데이터 업데이트
        post.title = form.title.data
        post.content = form.content.data
        post.category_id = form.category_id.data
        db.session.commit() 
        flash('Post 수정 완료!', category="success")
        return redirect(url_for('views.post', post_id=post_id))
    else:
        flash('Post 수정 실패!', category="error")
        return render_template(BASE_VIEWS_DIR + "post_write.html", 
            user=current_user, 
            form=form, 
            type="Edit",
            post_id=post_id,
        )

@views.route('/post-delete/<int:post_id>')
@login_required
def post_delete(post_id):
    # 쿼리 최대 4번 = user 1번 + post 삭제 1번 + user의 posts_count update 1번 + comments 삭제 1번
    # + comments 관련 user update N번
    # home 돌아옴 = 쿼리 최대 4번 = posts 3번 + user 1번
    post = db.session.get(get_model('post'), post_id)
    if post is None:
        flash('게시물을 찾을 수 없습니다.', 'error')
        return redirect(url_for('views.home'))
    
    # 작성자가 아니면 abort
    if current_user.id != post.author_id: return abort(403)

    db.session.delete(post)
    db.session.commit()
    flash('게시물이 성공적으로 삭제되었습니다.', 'success')
    return jsonify(message='success'), 200

# ------------------------------------------------------------ comment 관련 기능들 ------------------------------------------------------------
@views.route('/comment-create/<int:post_id>', methods=['POST'])
@login_required
def comment_create(post_id): 
    # POST 요청 = 쿼리 최대 4번 = user 1번 + comment 추가(post조회 + post_comments + user_comments update 3번)
    # post 읽기 돌아옴 = 쿼리 최대 6번 = post 3번 + post_comments 2번 + user 1번
    form = CommentForm()

    if request.method == 'GET':
        flash('잘못된 요청입니다.', category="error")
        return redirect(url_for('views.home'))
    
    if form.validate_on_submit():
        comment = get_model('comment')(
            content=form.content.data,
            author_id=current_user.id,
            post_id=post_id
        )
        db.session.add(comment)
        db.session.commit()
        flash('댓글 작성 성공!', category="success")
        return redirect(url_for('views.post', post_id=post_id))
    else:
        flash('댓글 작성 실패!', category="error")
        return redirect(url_for('views.post', post_id=post_id))

@views.route('/comment-edit/<int:comment_id>', methods=['POST'])
@login_required
def comment_edit(comment_id):
    # POST 요청 = 쿼리 최대 4번 = user 1번 + comment update 1번
    # post 읽기 돌아옴 = 쿼리 최대 6번 = post 3번 + post_comments 2번 + user 1번
    form = CommentForm()
    
    if request.method == 'GET':
        flash('잘못된 요청입니다.', category="error")
        return redirect(url_for('views.home'))
    
    comment = db.session.get(get_model('comment'), comment_id)
    if comment is None:
        flash('해당 댓글은 존재하지 않습니다.', category="error")
        return redirect(url_for('views.home'))
    
    if current_user.id != comment.author_id: return abort(403)

    if form.validate_on_submit():
        comment.content = form.content.data
        db.session.commit()
        flash('댓글 수정 완료!', category="success")
        return redirect(url_for('views.post', post_id=comment.post_id))
    else:
        flash('댓글 수정 실패!', category="error")
        return redirect(url_for('views.post', post_id=comment.post_id))
    

@views.route('/comment-delete/<int:comment_id>')
@login_required
def comment_delete(comment_id):
    # POST 요청 = 쿼리 최대 5번 = user 1번 + comment, post 로드 2번 + comment 관련 업데이트(post + user) 2번 
    # post 읽기 돌아옴 = 쿼리 최대 6번 = post 3번 + post_comments 2번 + user 1번
    comment = db.session.get(get_model('comment'), comment_id)
    if comment is None:
        flash('해당 댓글은 존재하지 않습니다.', 'error')
        return jsonify(message='error'), 400
    
    # 작성자가 아니면 abort
    if current_user.id != comment.author_id: return abort(403)

    db.session.delete(comment)
    db.session.commit()
    flash('댓글이 성공적으로 삭제되었습니다.', 'success')
    return jsonify(message='success'), 200