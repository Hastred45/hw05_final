from django.test import TestCase

from ..models import Group, Post, User


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост, проверяем длину',
            group=cls.group,
        )

    def test_post_correct_object_name(self):
        """Проверяем, что у модели постов корректно работает __str__."""
        self.assertEqual(self.post.text[:15], str(self.post))

    def test_group_correct_object_name(self):
        """Проверяем, что у модели групп корректно работает __str__."""
        self.assertEqual(self.group.title, str(self.group))

    def test_verbose_name(self):
        """verbose_name в полях совпадает с ожидаемым."""
        field_verboses = {
            'text': 'Содержание заметки',
            'pub_date': 'Дата публикации',
            'author': 'Автор',
            'group': 'Сообщество',
        }
        for value, expected in field_verboses.items():
            with self.subTest(value=value):
                self.assertEqual(
                    self.post._meta.get_field(value).verbose_name,
                    expected
                )

    def test_help_text(self):
        """help_text в полях совпадает с ожидаемым."""
        post_model = PostModelTest.post
        field_help_texts = {
            'text': 'Напишите о чем хотели рассказать',
            'group': 'Сообщество, к которому будет относиться пост',
        }
        for value, expected in field_help_texts.items():
            with self.subTest(value=value):
                self.assertEqual(
                    post_model._meta.get_field(value).help_text, expected)
