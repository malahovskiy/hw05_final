from django.test import TestCase, Client
from http import HTTPStatus
from django.urls import reverse


class StaticURLTests(TestCase):

    def setUp(self):
        self.guest = Client()

    def test_author(self):
        '''Тест страниц доступных гостю'''
        guest_urls = (
            reverse('about:author'),
            reverse('about:tech'),
        )
        for url in guest_urls:
            with self.subTest(url=url):
                response = self.guest.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)
