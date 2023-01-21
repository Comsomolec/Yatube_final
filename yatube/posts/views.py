from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import (
    render,
    get_object_or_404,
    redirect,
)
from django.views.decorators.cache import cache_page
from django.urls import reverse

from .forms import PostForm, CommentForm
from .models import Post, Group, User, Follow
from yatube.settings import POSTS_IN_PAGE


def paginator_page(list, request):
    return Paginator(
        list, POSTS_IN_PAGE).get_page(request.GET.get('page'))


@cache_page(20, key_prefix='index_page')
def index(request):
    return render(request, 'posts/index.html', {
        'page_obj': paginator_page(Post.objects.all(), request),
    })


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    return render(request, 'posts/group_list.html', {
        'group': group,
        'page_obj': paginator_page(group.posts.all(), request),
    })


def profile(request, username):
    author = get_object_or_404(User, username=username)
    return render(request, 'posts/profile.html', {
        'author': author,
        'page_obj': paginator_page(author.posts.all(), request),
        'following': request.user.is_authenticated
        and author.following.filter(user=request.user, author=author).exists(),
    })


def post_detail(request, post_id):
    return render(request, 'posts/post_detail.html', {
        'post': get_object_or_404(Post, id=post_id),
        'form': CommentForm(request.POST or None),
    })


@login_required
def post_create(request):
    form = PostForm(
        request.POST or None,
        request.FILES or None,
    )
    if not form.is_valid():
        return render(request, 'posts/create_post.html', {'form': form})

    post = form.save(commit=False)
    post.author = request.user
    post.save()
    return redirect(
        reverse('posts:profile', args=[request.user.username])
    )


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if post.author != request.user:
        return redirect('posts:post_detail', post_id)

    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if not form.is_valid():
        return render(
            request,
            'posts/create_post.html',
            {'form': form, 'post': post, },
        )

    form.save()
    return redirect('posts:post_detail', post_id)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id)


@login_required
def follow_index(request):
    return render(
        request,
        'posts/follow.html',
        {
            'page_obj': paginator_page(
                Post.objects.filter(author__following__user=request.user),
                request
            ),
            # 'authors': request.user.follower.all(),
        }
    )


@login_required
def profile_follow(request, username):
    user = request.user
    author = User.objects.get(username=username)
    if user.username != username and not Follow.objects.filter(
        user=user, author=author
    ).exists():
        Follow.objects.create(
            user=user, author=author
        )
    return redirect(
        reverse('posts:profile', args=[username])
    )


@login_required
def profile_unfollow(request, username):
    get_object_or_404(
        Follow, user=request.user,
        author=User.objects.get(username=username)
    ).delete()
    return redirect(
        reverse('posts:profile', args=[username])
    )
