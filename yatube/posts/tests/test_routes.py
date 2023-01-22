from django.test import TestCase
from django.urls import reverse

from ..urls import app_name


POST_ID = 1
SLUG = 'test_slug'
USER = 'author'

CASES = [
    ['/', 'main_page', []],
    [f'/group/{SLUG}/', 'group_posts', [SLUG]],
    [f'/profile/{USER}/', 'profile', [USER]],
    ['/create/', 'post_create', []],
    [f'/posts/{POST_ID}/', 'post_detail', [POST_ID]],
    [f'/posts/{POST_ID}/edit/', 'post_edit', [POST_ID]],
    [f'/posts/{POST_ID}/comment/', 'add_comment', [POST_ID]],
    ['/follow/', 'follow_index', []],
    [f'/profile/{USER}/follow/', 'profile_follow', [USER]],
    [f'/profile/{USER}/unfollow/', 'profile_unfollow', [USER]],
]


class PostRoutesTests(TestCase):
    def test_routes_calculation_get_correct_url(self):
        """Тестирование маршрутов, расчеты выдают ожидаемые URL"""

        for url, name, args in CASES:
            with self.subTest(url=url):
                self.assertEqual(
                    url,
                    reverse(
                        f"{app_name}:{name}", args=args
                    )
                )
