import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..forms import PostForm
from ..models import Group, Post, User, Comment

CREATE = reverse('posts:post_create')

# Создаем временную папку для медиа-файлов;
# на момент теста медиа папка будет переопределена
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


# Для сохранения media-файлов в тестах будет использоватьсяgs
# временная папка TEMP_MEDIA_ROOT, а потом мы ее удалим
@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user,
            group=cls.group,
        )
        cls.form = PostForm()

        cls.POST_PAGE = reverse('posts:post_detail', args=[cls.post.pk])
        cls.POST_EDIT = reverse('posts:post_edit', args=[cls.post.pk])
        cls.COMMENT = reverse('posts:add_comment', args=[cls.post.pk])

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
        self.guest_client = Client()
        self.user = User.objects.create_user(username='HasNoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.PROFILE = reverse('posts:profile', args=[self.user])

    def test_create_comment(self):
        comments_count = Comment.objects.count()
        form_data = {
            'text': 'Создаем коммент',
        }
        response = self.authorized_client.post(
            PostCreateFormTests.COMMENT,
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, self.POST_PAGE)
        self.assertEqual(Comment.objects.count(), comments_count + 1)

        self.assertTrue(
            Comment.objects.filter(
                text='Создаем коммент',
            ).last()
        )

    def test_create_post(self):
        """Валидная форма создает post."""
        posts_count = Post.objects.count()
        # Подготавливаем данные для передачи в форму
        image_post = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        upload = SimpleUploadedFile(
            name='small.gif',
            content=image_post,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Тестовый текст №2',
            'group': self.group.id,
            'image': upload,
        }
        response = self.authorized_client.post(
            CREATE,
            data=form_data,
            follow=True
        )
        # Проверяем, сработал ли редирект
        self.assertRedirects(response, self.PROFILE)
        # Проверяем, увеличилось ли число постов
        self.assertEqual(Post.objects.count(), posts_count + 1)

        self.assertTrue(
            Post.objects.filter(
                text='Тестовый текст №2',
                image='posts/small.gif'
            ).last()
        )
        self.assertTrue(
            Group.objects.filter(
                title='Тестовая группа',
                slug='test-slug',
                description='Тестовое описание',
            ).last()
        )

    def test_edit_post(self):
        """Валидная форма изменяет post."""
        # Подготавливаем данные для передачи в форму
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Измененный текст',
            'group': self.group.id,
        }
        self.authorized_client.force_login(self.post.author)
        response = self.authorized_client.post(
            PostCreateFormTests.POST_EDIT,
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, PostCreateFormTests.POST_PAGE)

        self.assertEqual(Post.objects.count(), posts_count)

        self.assertTrue(
            Post.objects.filter(
                text='Измененный текст',
            ).exists()
        )
        self.assertTrue(
            Group.objects.filter(
                title='Тестовая группа',
                slug='test-slug',
                description='Тестовое описание',
            ).exists()
        )
