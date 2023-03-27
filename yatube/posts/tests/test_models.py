from django.contrib.auth import get_user_model
from django.test import TestCase
from ..models import Group, Post
import shutil
import tempfile
from django.conf import settings
from django.core.cache import cache

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

User = get_user_model()


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
            text='Тестовый пост длинной больше 15 символов',
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        cache.clear()

    def test_models_correct_verbose_name(self):
        post = PostModelTest.post

        field_verboses = {
            'text': 'Текст поста',
            'pub_date': 'Дата создания',
            'author': 'Автор',
            'group': 'Группа',
        }

        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).verbose_name, expected_value
                )

    def test_models_correct_help_text(self):
        post = PostModelTest.post

        field_verboses = {
            'text': 'Введите текст поста. Текст не должен быть пустым.',
            'group': 'Группа, к которой относится пост.',
        }

        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).help_text, expected_value
                )

    def test_models_correct_str(self):
        str_len: int = 15  # количество символов в строке для __str__
        post = self.post
        group = self.group

        value_expected = {
            post.__str__(): post.text[:str_len],
            group.__str__(): group.title,
        }

        for value, expected in value_expected.items():
            with self.subTest(value=value):
                self.assertEqual(value, expected)
