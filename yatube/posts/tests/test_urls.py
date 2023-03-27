from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from posts.models import Post, Group
from django.urls import reverse
from http import HTTPStatus
from django.core.cache import cache
import shutil
import tempfile
from django.conf import settings

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.PostAuthor = User.objects.create_user(username='PostAuthor')
        cls.RandomUser = User.objects.create_user(username='RandomUser')

        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test-slug',
            description='Тестовое описание'
        )

        cls.post = Post.objects.create(
            text='Test',
            author=cls.PostAuthor,
            pk=1
        )

    def setUp(self):
        self.guest = Client()
        self.post_author = Client()
        self.post_author.force_login(self.PostAuthor)
        self.random_user = Client()
        self.random_user.force_login(self.RandomUser)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        cache.clear()

    def test_urls_guest(self):
        '''Тест страниц доступных гостю'''
        guest_allowed_urls = (
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.RandomUser}),
            reverse('posts:post_detail', kwargs={'post_id': self.post.pk}),
        )
        guest_redirect_urls = (
            reverse('posts:post_create'),
            reverse(
                'posts:post_edit',
                kwargs={'post_id': self.post.pk}),

            reverse(
                'posts:profile_follow',
                kwargs={'username': self.PostAuthor.username}),
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': self.PostAuthor.username}),
            reverse('posts:follow_index'),
        )

        for url in guest_allowed_urls:
            with self.subTest(url=url):
                response = self.guest.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)
        for url in guest_redirect_urls:
            with self.subTest(url=url):
                response = self.guest.get(url)
                self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_urls_random_user(self):
        '''Тест страниц доступных авторизованному пользователю'''
        random_user_allowed_urls = (
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.RandomUser}),
            reverse('posts:post_detail', kwargs={'post_id': self.post.pk}),
            reverse('posts:post_create'),
            reverse('posts:follow_index'),

        )
        random_user_redirect_urls = (
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk}),
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.PostAuthor.username}),
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': self.PostAuthor.username}),
        )
        for url in random_user_allowed_urls:
            with self.subTest(url=url):
                response = self.random_user.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)
        for url in random_user_redirect_urls:
            with self.subTest(url=url):
                response = self.random_user.get(url)
                self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_urls_post_author(self):
        '''Тест страниц доступных авторизованному пользователю автору'''
        post_author_allowed_urls = (
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.RandomUser}),
            reverse('posts:post_detail', kwargs={'post_id': self.post.pk}),
            reverse('posts:post_create'),
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk}),
            reverse('posts:follow_index'),
        )
        post_author_redirect_urls = {
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.PostAuthor.username}),
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': self.PostAuthor.username}),
        }
        for url in post_author_allowed_urls:
            with self.subTest(url=url):
                response = self.post_author.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)
        for url in post_author_redirect_urls:
            with self.subTest(url=url):
                response = self.random_user.get(url)
                self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_edit_guest_redirect(self):
        '''
        Гость будет перенаправлен на /auth/login/ с последующим
        перенаправлением на карточку поста
        '''
        response = self.guest.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk}),
            follow=True)
        self.assertRedirects(
            response, ('/auth/login/?next=/posts/1/edit/'))

    def test_edit_random_user(self):
        '''Не автор будет перенаправлени на карточку поста'''
        response = self.random_user.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk}),
            follow=True)
        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={'post_id': self.post.pk})
        )

    def test_unexisting_page(self):
        '''Тест несуществующей ссылки'''
        response = self.random_user.get('/some_randome_url/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_urls_uses_correct_templates(self):
        templates_url = {
            reverse(
                viewname='posts:index'
            ): 'posts/index.html',
            reverse(
                viewname='posts:group_list',
                kwargs={'slug': self.group.slug}
            ): 'posts/group_list.html',
            reverse(
                viewname='posts:profile',
                kwargs={'username': self.RandomUser}
            ): 'posts/profile.html',
            reverse(
                viewname='posts:post_detail',
                kwargs={'post_id': self.post.pk}
            ): 'posts/post_detail.html',
            reverse(
                viewname='posts:post_create'
            ): 'posts/create_post.html',
            reverse(
                viewname='posts:post_edit',
                kwargs={'post_id': self.post.pk}
            ): 'posts/create_post.html',
            '/some-random-url/': 'core/404.html',
        }
        for url, template in templates_url.items():
            with self.subTest(url=url):
                cache.clear()
                response = self.post_author.get(url)
                self.assertTemplateUsed(response, template)
