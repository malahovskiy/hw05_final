from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from posts.models import Post, Group, Follow
from django.urls import reverse
from django import forms
import shutil
import tempfile
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.core.cache import cache

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.PostAuthor = User.objects.create_user(username='PostAuthor')
        cls.RandomUser = User.objects.create_user(username='RandomUser')
        cls.Follower = User.objects.create_user(username='Follower')

        Follow.objects.create(user=cls.Follower, author=cls.PostAuthor)
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test-slug',
            description='Тестовое описание'
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            text='Test',
            author=cls.PostAuthor,
            group=cls.group,
            image=cls.uploaded,
            pk=1
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        cache.clear()

    def setUp(self):
        self.guest = Client()
        self.post_author = Client()
        self.post_author.force_login(self.PostAuthor)
        self.random_user = Client()
        self.random_user.force_login(self.RandomUser)
        self.follower = Client()
        self.follower.force_login(self.Follower)
        cache.clear()

    def test_new_post_on_right_places(self):
        '''Проверка того, что новый пост появляется на правильных местах'''
        test_group = Group.objects.create(
            title='Группа для теста',
            slug='second_slug',
            description='Группа для теста правильного расположения поста'
        )
        test_post = Post.objects.create(
            text='Текст для второго поста',
            author=self.PostAuthor,
            group=test_group,
            image=self.uploaded,
        )
        # Появился на главной странице
        cache.clear()
        response_index = self.random_user.get(reverse('posts:index'))
        self.assertIn(
            test_post,
            response_index.context['page_obj'],
            'Поста нет на главной странице'
        )
        # Появился в нужной группе
        cache.clear()
        response_group = self.random_user.get(
            reverse(
                viewname='posts:group_list',
                kwargs={'slug': test_group.slug, }
            )
        )
        self.assertIn(
            test_post,
            response_group.context['page_obj'],
            'Поста нет в нужной группе'
        )
        # На станице другой группы не появился
        cache.clear()
        response_other_group = self.random_user.get(
            reverse(
                viewname='posts:group_list',
                kwargs={'slug': self.group.slug, }
            )
        )
        self.assertNotIn(
            test_post,
            response_other_group.context['page_obj'],
            'Пост появился в другой группе'
        )
        # Появился у подписчика
        cache.clear()
        response_follow = self.follower.get(
            reverse(
                viewname='posts:follow_index'
            )
        )
        self.assertIn(
            test_post,
            response_follow.context['page_obj'],
            'Поста нет у подписчика'
        )
        # Не появился у других
        cache.clear()
        response_follow = self.random_user.get(
            reverse(
                viewname='posts:follow_index'
            )
        )
        self.assertNotIn(
            test_post,
            response_follow.context['page_obj'],
            'Поста появился у не подписчика'
        )

    def test_follow_user(self):
        self.random_user.get(
            reverse('posts:profile_follow',
                    kwargs={'username': self.PostAuthor.username}
                    )
        )
        self.assertTrue(
            Follow.objects.filter(
                user=self.RandomUser).filter(author=self.PostAuthor)
        )

    def test_follow_guest(self):
        response = self.guest.get(
            reverse('posts:profile_follow',
                    kwargs={'username': self.PostAuthor.username}
                    )
        )
        self.assertRedirects(
            response,
            reverse('users:login')
            + '?next='
            + reverse(
                viewname='posts:profile_follow',
                kwargs={'username': self.PostAuthor.username}
            )
        )

    def test_views_uses_correct_templates_for_user(self):
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
        }
        for url, template in templates_url.items():
            with self.subTest(url=url):
                cache.clear()
                response = self.post_author.get(url)
                self.assertTemplateUsed(
                    response,
                    template,
                    'Применен неправильный шаблон'
                )

    def test_views_uses_correct_templates_for_guest(self):
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

        }
        for url, template in templates_url.items():
            with self.subTest(template):
                cache.clear()
                response = self.guest.get(url)
                self.assertTemplateUsed(
                    response,
                    template,
                    f'Применен неправильный шаблон \n'
                    f'+ {template}\n'
                    f'- {response.templates}'
                )

    def post_context(self, page_obj):
        with self.subTest(post=page_obj):
            self.assertEqual(
                page_obj.text,
                self.post.text,
                'Проверьте текст'
            )
            self.assertEqual(
                page_obj.author,
                self.post.author,
                'Проверьте автора'
            )
            self.assertEqual(
                page_obj.group,
                self.post.group,
                'Проверьте группу'
            )
            self.assertEqual(
                page_obj.image,
                self.post.image,
                'Проверьте изображение'
            )

    def test_context_index(self):
        """Главная страница сформирована с правильным контекстом"""
        response = self.random_user.get(reverse('posts:index'))
        self.post_context(response.context['page_obj'][0])

    def test_cache_index(self):
        """Тест кэширования главной страницы"""
        url = reverse('posts:index')
        response_first = self.guest.get(url)
        empty_content = response_first.content
        Post.objects.create(
            text='Тествовый текст',
            author=self.PostAuthor
        )
        response_second = self.guest.get(url)
        cached_content = response_second.content
        self.assertEqual(empty_content, cached_content)
        cache.clear()
        response_third = self.guest.get(url)
        new_content = response_third.content
        self.assertNotEqual(cached_content, new_content)

    def test_context_group_list(self):
        response = self.random_user.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug})
        )
        self.post_context(response.context['post'])

    def test_context_profile(self):
        response = self.random_user.get(
            reverse(
                'posts:profile',
                kwargs={'username': self.PostAuthor.username})
        )
        self.post_context(response.context['post'])

    def test_context_post_detail(self):
        response = self.random_user.get(
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.pk}
            )
        )
        self.post_context(response.context['post'])

    def test_form(self):
        context = {
            reverse('posts:post_create'),
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk})
        }
        for reverse_page in context:
            with self.subTest(reverse_page=reverse_page):
                cache.clear()
                response = self.post_author.get(reverse_page)
                self.assertIsInstance(
                    response.context['form'].fields['text'],
                    forms.fields.CharField,
                    'Неправильный тип поля'
                )
                self.assertIsInstance(
                    response.context['form'].fields['group'],
                    forms.fields.ChoiceField,
                    'Неправильный тип поля'
                )


class PaginatorViewsTest(TestCase):

    @classmethod
    def setUpClass(cls):
        post_num: int = 13  # Число постов для теста
        super().setUpClass()
        cls.PostAuthor = User.objects.create_user(username='PostAuthor')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test-slug',
            description='Тестовое описание'
        )

        post_list = [Post(
            text=f'{post_counter}',
            author=cls.PostAuthor,
            group=cls.group
        ) for post_counter in range(post_num)]

        Post.objects.bulk_create(post_list)

    def setUp(self):
        cache.clear()
        self.user = Client()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cache.clear()

    def test_first_page_contains_ten_records(self):
        response = self.user.get(reverse('posts:index'))
        # Проверка: количество постов на первой странице равно 10.
        self.assertEqual(
            len(response.context['page_obj']),
            10,
            'Неправильное количество элементов на странице'
        )

    def test_second_page_contains_three_records(self):
        # Проверка: на второй странице должно быть три поста.
        response = self.user.get(reverse('posts:index') + '?page=2')
        self.assertEqual(
            len(response.context['page_obj']),
            3,
            'Неправильное количество элементов на странице'
        )
