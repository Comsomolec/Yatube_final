from django.test import TestCase
from django.urls import reverse

from ..urls import app_name


POST_ID = 1
SLUG = 'test_slug'
USER = 'author'

CASES = [
    ['/', 'main_page', []],
    ['/group/test_slug/', 'group_posts', ['test_slug']],
    ['/profile/author/', 'profile', ['author']],
    ['/create/', 'post_create', []],
    ['/posts/1/', 'post_detail', [1]],
    ['/posts/1/edit/', 'post_edit', [1]],
    ['/posts/1/comment/', 'add_comment', [1]],
    ['/follow/', 'follow_index', []],
    ['/profile/author/follow/', 'profile_follow', ['author']],
    ['/profile/author/unfollow/', 'profile_unfollow', ['author']],
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
