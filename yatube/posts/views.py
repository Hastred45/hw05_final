from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User


def index(request):
    template = 'posts/index.html'
    title = "Последние обновления на сайте"
    post_list = Post.objects.all().order_by('-pub_date')
    paginator = Paginator(post_list, settings.PAGE_SIZE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'title': title,
        'page_obj': page_obj,
    }
    return render(request, template, context)


@login_required
def follow_index(request):
    template = 'posts/follow.html'
    title = "Ваши подписки"
    post_list = Post.objects.filter(
        author__following__user=request.user
    ).order_by('-pub_date')
    paginator = Paginator(post_list, settings.PAGE_SIZE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
        'title': title,
    }
    return render(request, template, context)


def group_posts(request, gr):
    template = 'posts/group_list.html'
    group = get_object_or_404(Group, slug=gr)
    post_list = group.group_list.order_by('-pub_date')
    paginator = Paginator(post_list, settings.PAGE_SIZE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, template, context)


def profile(request, username):
    template = 'posts/profile.html'
    author = get_object_or_404(User, username=username)
    author_list = Post.objects.filter(
        author=author
    ).order_by('-pub_date')
    paginator = Paginator(author_list, settings.PAGE_SIZE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    following = False
    if request.user.is_authenticated:
        follow_obj = Follow.objects.filter(user=request.user,
                                           author=author)
        if follow_obj:
            following = True
    context = {
        'page_obj': page_obj,
        'author': author,
        'following': following,
    }
    return render(request, template, context)


def post_detail(request, post_id):
    template = 'posts/post_detail.html'
    one_post = get_object_or_404(Post, pk=post_id)
    form = CommentForm()
    comments = one_post.comments.all()
    if one_post.author == request.user:
        is_author = True
    else:
        is_author = False
    context = {
        'one_post': one_post,
        'is_author': is_author,
        'comments': comments,
        'form': form,
    }
    return render(request, template, context)


@login_required
def post_create(request):
    template = 'posts/post_create.html'
    form = PostForm(request.POST, files=request.FILES or None)
    if not form.is_valid():
        return render(request, template, context={'form': form})
    form = form.save(commit=False)
    form.author = request.user
    form.save()
    return redirect('posts:profile', form.author)


@login_required
def post_edit(request, post_id):
    template = 'posts/post_create.html'
    post = get_object_or_404(Post, pk=post_id)
    if request.user == post.author:
        is_edit = True
        form = PostForm(
            request.POST or None,
            files=request.FILES or None,
            instance=post
        )
        if not form.is_valid():
            return render(
                request,
                template,
                context={'form': form, 'is_edit': is_edit}
            )
        form = form.save()
        return redirect('posts:post_detail', post_id)
    else:
        return redirect('posts:post_detail', post_id)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    Follow.objects.create(user=request.user, author=author)
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    follow = Follow.objects.get(user=request.user,
                                author=author)
    follow.delete()
    return redirect('posts:profile', username=username)
