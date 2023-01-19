from django.test import TestCase, Client
from django.urls import reverse


class StaticPagesViewTests(TestCase):
    def setUp(self):
        super().setUpClass()
        self.guest_client = Client()

    def test_pages_about_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""

        templates_page = {
            reverse("about:author"): "about/author.html",
            reverse("about:tech"): "about/tech.html",
        }
        for reverse_name, template in templates_page.items():
            with self.subTest(template=template):
                response = self.guest_client.get(reverse_name)
                self.assertTemplateUsed(response, template)
