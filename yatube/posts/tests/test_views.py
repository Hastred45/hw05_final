import shutil
import tempfile

from django import forms
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.core.cache import cache

from ..models import Group, Post, User, Comment, Follow

MAIN = reverse('posts:index')
CREATE = reverse('posts:post_create')
GROUP_SLUG = 'test-slug'
GROUP_LIST = reverse('posts:group_list', args=[GROUP_SLUG])
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
FOLLOW_INDEX = reverse('posts:follow_index')


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='auth')
        image_post = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        cls.upload = SimpleUploadedFile(
            name='small.gif',
            content=image_post,
            content_type='image/gif'
        )
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        for cls.post_list in range(13):
            cls.post = Post.objects.create(
                text='Тестовый текст',
                author=cls.author,
                group=cls.group,
                image=cls.upload
            )
        cls.PROFILE = reverse('posts:profile', args=[cls.post.author])
        cls.POST_PAGE = reverse('posts:post_detail', args=[cls.post.pk])
        cls.POST_EDIT = reverse('posts:post_edit', args=[cls.post.pk])
        cls.COMMENT = reverse('posts:add_comment', args=[cls.post.pk])
        cls.FOLLOW = reverse('posts:profile_follow', args=[cls.post.author])
        cls.UNFOLLOW = reverse('posts:profile_unfollow',
                               args=[cls.post.author])

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        # Модуль shutil - библиотека Python с прекрасными инструментами
        # для управления файлами и директориями:
        # создание, удаление, копирование, перемещение, изменение
        # папок и файлов
        # Метод shutil.rmtree удаляет директорию и всё её содержимое
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        # Создаём неавторизованный клиент
        self.guest_client = Client()
        # Создаём авторизованный клиент
        self.user_1 = User.objects.create_user(username='HasNoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user_1)

    def test_follow_new_post_appears_in_index(self):
        self.post_author = Post.objects.create(
            text='Проверка подписок',
            author=self.author
        )
        self.follow = Follow.objects.create(
            user=self.user_1, author=self.author
        )
        follow_index = self.authorized_client.get(FOLLOW_INDEX)
        self.assertIn('Проверка подписок', follow_index.content.decode())

    def test_not_follow_new_post_not_appears_in_index(self):
        self.post_author = Post.objects.create(
            text='Проверка подписок',
            author=self.author
        )
        follow_index = self.authorized_client.get(FOLLOW_INDEX)
        self.assertNotIn('Проверка подписок', follow_index.content.decode())

    def check_post_in_page(self, url, text, user, group):
        response = self.authorized_client.get(url)
        post_0 = response.context['page_obj'][0]
        self.assertEqual(post_0.text, text)
        self.assertEqual(post_0.author, user)
        self.assertEqual(post_0.group, group)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_page_names = {
            MAIN: 'posts/index.html',
            GROUP_LIST: 'posts/group_list.html',
            CREATE: 'posts/post_create.html',
            PostPagesTests.PROFILE: 'posts/profile.html',
            PostPagesTests.POST_PAGE: 'posts/post_detail.html',
        }
        for reverse_name, template in templates_page_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_edit_page_uses_correct_template(self):
        """
        namespase:name "posts:post_edit" использует шаблон
        posts/post_create.html.
        """
        self.authorized_client.force_login(self.author)
        response = self.authorized_client.get(PostPagesTests.POST_EDIT)
        self.assertTemplateUsed(response, 'posts/post_create.html')

    def test_index_context_and_paginator(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(MAIN)
        first_object = response.context['page_obj'][0]
        first_object_items = {
            first_object.text: self.post.text,
            first_object.author: self.post.author,
            first_object.group: self.post.group,
            first_object.image: self.post.image,
        }
        for test, result in first_object_items.items():
            with self.subTest(result=result):
                self.assertEqual(test, result)

        self.assertEqual(
            response.context.get('title'), 'Последние обновления на сайте'
        )

        self.assertEqual(len(response.context['page_obj']), settings.PAGE_SIZE)

        response = self.guest_client.get(reverse('posts:index') + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 3)

    def test_post_list_context_and_paginator(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(GROUP_LIST)
        first_object = response.context['page_obj'][0]
        first_object_items = {
            first_object.text: self.post.text,
            first_object.author: self.post.author,
            first_object.group: self.post.group,
            first_object.image: self.post.image,
        }
        for test, result in first_object_items.items():
            with self.subTest(result=result):
                self.assertEqual(test, result)

        group_object = response.context['group']
        group_object_items = {
            group_object.title: self.group.title,
            group_object.slug: self.group.slug,
            group_object.description: self.group.description,
        }
        for test, result in group_object_items.items():
            with self.subTest(result=result):
                self.assertEqual(test, result)

        self.assertIsNotNone(first_object.image)
        self.assertEqual(len(response.context['page_obj']), settings.PAGE_SIZE)

        response = self.guest_client.get(reverse('posts:index') + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 3)

    def test_profile_context_and_paginator(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(PostPagesTests.PROFILE)
        first_object = response.context['page_obj'][0]
        first_object_items = {
            first_object.text: self.post.text,
            first_object.author: self.post.author,
            first_object.group: self.post.group,
            first_object.image: self.post.image,
        }
        for test, result in first_object_items.items():
            with self.subTest(result=result):
                self.assertEqual(test, result)

        self.assertIsNotNone(first_object.image)
        self.assertEqual(
            response.context.get('author'), self.post.author
        )

        self.assertEqual(len(response.context['page_obj']), settings.PAGE_SIZE)

        response = self.guest_client.get(reverse('posts:index') + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 3)

    def test_post_detail_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(PostPagesTests.POST_PAGE)
        one_post = response.context['one_post']
        one_object_items = {
            one_post.text: self.post.text,
            one_post.author: self.post.author,
            one_post.group: self.post.group,
            one_post.image: self.post.image,
        }
        for test, result in one_object_items.items():
            with self.subTest(result=result):
                self.assertEqual(test, result)

        self.assertIsNotNone(one_post.image)
        self.assertEqual(
            response.context.get('is_author'), False
        )

    def test_create_post_context(self):
        """Шаблон create_post сформирован с правильным контекстом."""
        response = self.authorized_client.get(CREATE)
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_edit_post_context(self):
        """
        Шаблон post_edit сформирован с правильным
        контекстом для редактирования.
        """
        self.authorized_client.force_login(self.author)
        response = self.authorized_client.get(PostPagesTests.POST_EDIT)
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

        self.assertEqual(
            response.context.get('is_edit'), True
        )

    def test_post_in_the_pages(self):
        """Доп проверка при создании поста"""
        urls = (MAIN,
                PostPagesTests.PROFILE,
                GROUP_LIST)

        for url in urls:
            with self.subTest(url=url):
                self.check_post_in_page(
                    url, 'Тестовый текст', self.post.author, self.post.group
                )

    def test_cache_index(self):
        post = Post.objects.create(
            text='Тест кэша',
            author=self.author,
            group=self.group,
            image=self.upload,
        )
        response_1 = self.authorized_client.get(MAIN)
        post.delete()
        response_2 = self.authorized_client.get(MAIN)
        self.assertEqual(response_1.content, response_2.content)
        cache.clear()
        response_3 = self.authorized_client.get(MAIN)
        self.assertNotEqual(response_1.content, response_3.content)

    def test_auth_can_comment(self):
        self.authorized_client.post(
            PostPagesTests.COMMENT,
            {'text': 'test_text'}
        )
        post_with_comment = self.authorized_client.get(
            PostPagesTests.POST_PAGE
        )
        self.assertIn('test_text', post_with_comment.content.decode())
        comment_obj = Comment.objects.filter(
            author=self.user_1, post=self.post.pk
        ).count()
        self.assertEqual(comment_obj, 1)

    def test_guest_cant_comment(self):
        self.guest_client.post(
            PostPagesTests.COMMENT,
            {'text': 'test_text'}
        )
        post_with_comment = self.authorized_client.get(
            PostPagesTests.POST_PAGE
        )
        self.assertNotIn('test_text', post_with_comment.content.decode())
        comment_obj = Comment.objects.filter(
            author=self.author, post=self.post.pk
        ).count()
        self.assertEqual(comment_obj, 0)

    def test_following(self):
        self.authorized_client.post(PostPagesTests.FOLLOW, follow=True)
        follow = Follow.objects.filter(user=self.user_1,
                                       author=self.author).count()
        self.assertEqual(follow, 1)
        self.authorized_client.post(PostPagesTests.UNFOLLOW, follow=True)
        follow = Follow.objects.filter(user=self.user_1,
                                       author=self.author).count()
        self.assertEqual(follow, 0)
