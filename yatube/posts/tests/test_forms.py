import shutil
import tempfile
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.core.cache import cache

from django.urls import reverse
from django.contrib.auth import get_user_model


from ..models import Post, Group, Comment

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.TestUser = User.objects.create_user(username='user')
        cls.TestGroup = Group.objects.create(
            title='Тестовая группа',
            description='Тестовое описание',
            slug='test_slug'
        )

        cls.img_origin = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.img_new = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x01\x3B'
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        cache.clear()

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.TestUser)

    def test_create_post_for_user(self):
        """Проверка работы формы сознания поста для пользователя"""
        post_count = Post.objects.count()
        uploaded = SimpleUploadedFile(
            name='img_origin.gif',
            content=self.img_origin,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Тестовый текст',
            'group': self.TestGroup.id,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse(
                'posts:profile',
                kwargs={'username': self.TestUser.username}
            )
        )
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text=form_data['text'],
                group=self.TestGroup,
                image=f'posts/{uploaded}',
            ).exists()
        )

    def test_create_post_for_guest(self):
        """Проверка работы формы сознания поста для гостя"""
        post_count = Post.objects.count()
        uploaded = SimpleUploadedFile(
            name='img_origin.gif',
            content=self.img_origin,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Тестовый текст',
            'group': self.TestGroup.id,
            'image': uploaded
        }
        response = self.guest_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('users:login') + '?next=' + reverse('posts:post_create')
        )
        self.assertEqual(Post.objects.count(), post_count)
        self.assertFalse(
            Post.objects.filter(
                text=form_data['text'],
                group=self.TestGroup,
                image=f'posts/{uploaded}',
            ).exists()
        )

    def test_edit_post_for_user(self):
        """Проверка работы формы редактирования для пользователя"""
        uploaded = SimpleUploadedFile(
            name='img_origin.gif',
            content=self.img_origin,
            content_type='image/gif'
        )
        new_uploaded = SimpleUploadedFile(
            name='img_new.gif',
            content=self.img_new,
            content_type='image/gif'
        )
        post = Post.objects.create(
            text='Тестовый текст',
            author=self.TestUser,
            group=self.TestGroup,
            image=uploaded,
        )
        post_count = Post.objects.count()

        form_data = {
            'text': 'Новый текст',
            'group': self.TestGroup.id,
            'image': new_uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': post.pk}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse(
                'posts:post_detail',
                kwargs={'post_id': post.id}
            )
        )
        self.assertEqual(Post.objects.count(), post_count)
        self.assertTrue(
            Post.objects.filter(
                text=form_data['text'],
                group=self.TestGroup,
                image=f'posts/{new_uploaded}',
            ).exists()
        )

    def test_edit_post_for_guest(self):
        """Проверка работы формы редактирования для гостя"""
        uploaded = SimpleUploadedFile(
            name='img_origin.gif',
            content=self.img_origin,
            content_type='image/gif'
        )
        new_uploaded = SimpleUploadedFile(
            name='img_new.gif',
            content=self.img_new,
            content_type='image/gif'
        )
        post = Post.objects.create(
            text='Тестовый текст',
            author=self.TestUser,
            group=self.TestGroup,
            image=uploaded
        )
        post_count = Post.objects.count()
        form_data = {
            'text': 'Новый текст',
            'group': self.TestGroup.id,
            'image': new_uploaded,
        }
        response = self.guest_client.post(
            reverse('posts:post_edit', kwargs={'post_id': post.pk}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('users:login') + '?next='
            + reverse('posts:post_edit', kwargs={'post_id': post.pk})
        )
        self.assertEqual(Post.objects.count(), post_count)
        self.assertFalse(
            Post.objects.filter(
                text=form_data['text'],
                group=self.TestGroup,
                image=f'posts/{new_uploaded}',
            ).exists()
        )


class CommentCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.TestUser = User.objects.create_user(username='user')
        cls.TestGroup = Group.objects.create(
            title='Тестовая группа',
            description='Тестовое описание',
            slug='test_slug'
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.TestUser)

    def test_comment_add_user(self):
        post = Post.objects.create(
            text='Тестовый текст',
            author=self.TestUser,
            group=self.TestGroup
        )
        form_data = {
            'post': post,
            'author': self.authorized_client,
            'text': 'Тестовый комментарий',
        }
        comment_count = Comment.objects.count()
        self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': post.pk}),
            data=form_data,
            follow=True
        )
        self.assertTrue(
            (Comment.objects.filter(
                post=post,
                author=self.TestUser,
                text=form_data['text']).exists())
            and (Comment.objects.count() == comment_count + 1)
        )

    def test_comment_add_guest(self):
        post = Post.objects.create(
            text='Тестовый текст',
            author=self.TestUser,
            group=self.TestGroup
        )
        form_data = {
            'post': post,
            'author': self.authorized_client,
            'text': 'Тестовый комментарий',
        }
        comment_count = Comment.objects.count()
        response = self.guest_client.post(
            reverse('posts:add_comment', kwargs={'post_id': post.pk}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('users:login')
            + '?next='
            + reverse('posts:add_comment', kwargs={'post_id': post.pk}))

        self.assertTrue(
            not Comment.objects.filter(
                post=post,
                author=self.TestUser,
                text=post.text).exists()
            and Comment.objects.count() == comment_count

        )
