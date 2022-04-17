from http import HTTPStatus

from django.test import Client, TestCase

from ..models import Group, Post, User

MAIN = '/'
CREATE = '/create/'
GROUP_SLUG = 'test-slug'
GROUP_LIST = f'/group/{GROUP_SLUG}/'
NOT_FOUND_404 = '/unexisting_page/'


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug=GROUP_SLUG,
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user,
            group=cls.group,
        )
        cls.PROFILE = f'/profile/{cls.post.author}/'
        cls.POST_PAGE = f'/posts/{cls.post.pk}/'
        cls.POST_EDIT = f'/posts/{cls.post.pk}/edit/'

    def setUp(self):
        self.guest_client = Client()
        self.user_1 = User.objects.create_user(username='HasNoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user_1)

    def test_urls_guest_client(self):
        """Проверям страницы доступные без авторизации."""
        url_names = (
            MAIN,
            GROUP_LIST,
            PostsURLTests.PROFILE,
            PostsURLTests.POST_PAGE,
        )
        for address in url_names:
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_authorized_client(self):
        """Проверям страницы доступные с авторизацией."""
        response = self.authorized_client.get(CREATE)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        response = self.authorized_client.get(PostsURLTests.PROFILE)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_url_author(self):
        """Страница posts/<post_id>/edit/ доступна только автору"""
        self.authorized_client.force_login(self.post.author)
        response = self.authorized_client.get(PostsURLTests.POST_EDIT)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            MAIN: 'posts/index.html',
            GROUP_LIST: 'posts/group_list.html',
            CREATE: 'posts/post_create.html',
            PostsURLTests.PROFILE: 'posts/profile.html',
            PostsURLTests.POST_PAGE: 'posts/post_detail.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_template_author(self):
        """Страница posts/<post_id>/edit/ использует правильный шаблон"""
        self.authorized_client.force_login(self.post.author)
        response = self.authorized_client.get(PostsURLTests.POST_EDIT)
        self.assertTemplateUsed(response, 'posts/post_create.html')

    def test_url_404(self):
        """Проверяем 404"""
        response = self.guest_client.get(NOT_FOUND_404)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertTemplateUsed(response, 'core/404.html')
