from django.test import TestCase
from django.urls import reverse

from ..apps import PostsConfig


POST_ID = 1
SLUG = 'test_slug'
USER = 'author'

CASES = [
    ['/', 'main_page', []],
    ['/group/test_slug/', 'group_posts', [SLUG]],
    ['/profile/author/', 'profile', [USER]],
    ['/create/', 'post_create', []],
    ['/posts/1/', 'post_detail', [POST_ID]],
    ['/posts/1/edit/', 'post_edit', [POST_ID]],
    ['/posts/1/comment/', 'add_comment', [POST_ID]],
    ['/follow/', 'follow_index', []],
    ['/profile/author/follow/', 'profile_follow', [USER]],
    ['/profile/author/unfollow/', 'profile_unfollow', [USER]],
]


class PostRoutesTests(TestCase):
    def test_routes_calculation_get_correct_url(self):
        """Тестирование маршрутов, расчеты выдают ожидаемые URL"""

        for url, name, arg in CASES:
            with self.subTest(url=url):
                self.assertEqual(
                    url,
                    reverse(
                        f"{PostsConfig.name}:{name}", args=arg
                    )
                )
