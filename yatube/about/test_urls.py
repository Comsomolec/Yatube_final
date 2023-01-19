from http import HTTPStatus

from django.test import TestCase, Client


class StaticPagesURLTests(TestCase):
    def setUp(self):
        super().setUpClass()
        self.guest_client = Client()

    def test_about_url_exists_at_desired_location(self):
        """Проверка доступности адресов статических страниц."""
        test_response = {
            'author': '/about/author/',
            'tech': '/about/tech/',
        }
        for field, urls in test_response.items():
            with self.subTest(field=field):
                response = self.guest_client.get(urls)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_about_url_uses_correct_template(self):
        """Проверка шаблона для адресов статических страниц."""
        test_response = {
            '/about/author/': 'about/author.html',
            '/about/tech/': 'about/tech.html',
        }
        for urls, page in test_response.items():
            with self.subTest(urls=urls):
                response = self.guest_client.get(urls)
                self.assertTemplateUsed(
                    response, page
                )
