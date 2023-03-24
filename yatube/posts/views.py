from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from .models import Post, Group, Follow
from django.core.paginator import Paginator
from django.contrib.auth import get_user_model
from .forms import PostForm, CommentForm
from django.core.cache import cache
from django.core.cache.utils import make_template_fragment_key

User = get_user_model()

POSTS_COUNT: int = 10


def index(request):
    """Функция обработки запроса к главной странице"""

    template = 'posts/index.html'
    posts = Post.objects.select_related()
    paginator = Paginator(posts, POSTS_COUNT)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
    }

    return render(request, template, context)


def group_posts(request, slug):
    """Функция обработки запроса к странице группы"""

    template = 'posts/group_list.html'
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.select_related('group')
    paginator = Paginator(posts, POSTS_COUNT)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, template, context)


def profile(request, username):
    template = 'posts/profile.html'
    author = User.objects.get(username=username)
    posts = author.posts.select_related('author')
    paginator = Paginator(posts, POSTS_COUNT)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    posts_count = paginator.count
    following = (
        request.user.is_authenticated
        and Follow.objects.filter(user=request.user).filter(author=author)
    )

    context = {
        'page_obj': page_obj,
        'posts_count': posts_count,
        'author': author,
        'following': following,
    }
    return render(request, template, context)


def post_detail(request, post_id):
    template = 'posts/post_detail.html'
    post = Post.objects.get(pk=post_id)
    author = User.objects.get(username=post.author)
    post_count = author.posts.count()
    context = {
        'form': CommentForm(request.POST or None),
        'comments': post.comments.select_related('post'),
        'post': post,
        'post_count': post_count,
    }
    return render(request, template, context)


@login_required
def post_create(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', post.author.username)
    form = PostForm()
    context = {
        'form': form,
        'group_list': Group.objects.all()
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def post_edit(request, post_id):
    is_edit: bool = True
    post = get_object_or_404(Post, id=post_id)

    if (post.author != request.user):
        return redirect('posts:post_detail', post_id)
    if request.method == 'POST':
        form = PostForm(
            request.POST,
            instance=post,
            files=request.FILES or None
        )
        if form.is_valid():
            post.save()
            return redirect('posts:post_detail', post_id)
        return render(request, 'posts/create_post.html', {'form': form})
    form = PostForm(instance=post)
    context = {
        'form': form,
        'is_edit': is_edit,
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)

# posts/views.py


@login_required
def follow_index(request):
    template = 'posts/follow.html'
    follower = User.objects.get(username=request.user)
    posts = Post.objects.filter(
        author__following__user=follower
    )
    paginator = Paginator(posts, POSTS_COUNT)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
    }
    return render(request, template, context)


@login_required
def profile_follow(request, username):
    user = User.objects.get(username=request.user)
    author = User.objects.get(username=username)
    if author != user:
        Follow.objects.get_or_create(
            user=user,
            author=author,
        )
    cache.delete(make_template_fragment_key('follow_posts'))
    return redirect('posts:profile', username)


@login_required
def profile_unfollow(request, username):
    user = User.objects.get(username=request.user)
    author = User.objects.get(username=username)
    Follow.objects.filter(
        user=user,
        author=author,
    ).delete()
    cache.delete(make_template_fragment_key('follow_posts'))
    return redirect('posts:follow_index')
