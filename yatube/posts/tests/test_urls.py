from http import HTTPStatus

from django.core.cache import cache
from django.test import TestCase, Client
from django.urls import reverse

from ..models import Group, Post, User

TEST_SLUG = 'test_slug'
TEST_USERNAME = 'Author_post'

INDEX_URL = reverse('posts:main_page')
CREATE_URL = reverse('posts:post_create')
PROFILE_URL = reverse('posts:profile', args=[TEST_USERNAME])
GROUP_LIST_URL = reverse('posts:group_posts', args=[TEST_SLUG])
FOLLOW_INDEX = reverse('posts:follow_index')
FOLLOW_URL = reverse('posts:profile_follow', args=[TEST_USERNAME])
UNFOLLOW_URL = reverse('posts:profile_unfollow', args=[TEST_USERNAME])
LOGIN = reverse('users:login')
UNEXISTING_PAGE: str = '/unexisting_page/'
CREATE_REDIRECT_LOGIN = f'{LOGIN}?next={CREATE_URL}'
FOLLOW_INDEX_REDIRECT_LOGIN = f'{LOGIN}?next={FOLLOW_INDEX}'
FOLLOW_REDIRECT_LOGIN = f'{LOGIN}?next={FOLLOW_URL}'
UNFOLLOW_REDIRECT_LOGIN = f'{LOGIN}?next={UNFOLLOW_URL}'
NOT_FOUND = HTTPStatus.NOT_FOUND
FOUND = HTTPStatus.FOUND
OK = HTTPStatus.OK


class PostURLTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=TEST_USERNAME)
        cls.auth_user = User.objects.create_user(username='Auth_user')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug=TEST_SLUG,
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group
        )
        cls.POST_DETAIL_URL = reverse(
            'posts:post_detail',
            args=[cls.post.pk]
        )
        cls.POST_EDIT_URL = reverse(
            'posts:post_edit',
            args=[cls.post.pk]
        )
        cls.EDIT_REDIRECT_LOGIN = f'{LOGIN}?next={cls.POST_EDIT_URL}'

        cls.guest = Client()
        cls.another = Client()
        cls.another.force_login(cls.auth_user)
        cls.author = Client()
        cls.author.force_login(cls.user)

    def setUp(self):
        cache.clear()

    def test_url_exists_for_users(self):
        """Проверка доступности адресов страниц для пользователей."""

        cases_list = [
            [UNEXISTING_PAGE, self.guest, NOT_FOUND],
            [INDEX_URL, self.guest, OK],
            [GROUP_LIST_URL, self.guest, OK],
            [PROFILE_URL, self.guest, OK],
            [self.POST_DETAIL_URL, self.guest, OK],
            [CREATE_URL, self.guest, FOUND],
            [CREATE_URL, self.another, OK],
            [self.POST_EDIT_URL, self.guest, FOUND],
            [self.POST_EDIT_URL, self.another, FOUND],
            [self.POST_EDIT_URL, self.author, OK],
            [FOLLOW_INDEX, self.guest, FOUND],
            [FOLLOW_INDEX, self.another, OK],
            [FOLLOW_URL, self.guest, FOUND],
            [FOLLOW_URL, self.another, FOUND],
            [FOLLOW_URL, self.author, FOUND],
            [UNFOLLOW_URL, self.guest, FOUND],
            [UNFOLLOW_URL, self.another, FOUND],
            [UNFOLLOW_URL, self.author, NOT_FOUND],
        ]
        for url, client, status in cases_list:
            with self.subTest(url=url, client=client):
                self.assertEqual(
                    client.get(url).status_code,
                    status
                )

    def test_redirect_on_create_and_edit(self):
        """Проверка редиректа пользователей."""

        cases_list = [
            [CREATE_URL, self.guest, CREATE_REDIRECT_LOGIN],
            [self.POST_EDIT_URL, self.guest, self.EDIT_REDIRECT_LOGIN],
            [self.POST_EDIT_URL, self.another, self.POST_DETAIL_URL],
            [FOLLOW_INDEX, self.guest, FOLLOW_INDEX_REDIRECT_LOGIN],
            [FOLLOW_URL, self.guest, FOLLOW_REDIRECT_LOGIN],
            [FOLLOW_URL, self.another, PROFILE_URL],
            [FOLLOW_URL, self.author, PROFILE_URL],
            [UNFOLLOW_URL, self.guest, UNFOLLOW_REDIRECT_LOGIN],
            [UNFOLLOW_URL, self.another, PROFILE_URL],
        ]
        for url, user, redirect_url in cases_list:
            with self.subTest(url=url, user=user):
                self.assertRedirects(
                    user.get(url, follow=True),
                    redirect_url
                )

    def test_url_uses_correct_template(self):
        """Проверка, что URL-адрес использует соответствующий шаблон."""

        templates_url = [
            [INDEX_URL, self.author, 'posts/index.html'],
            [GROUP_LIST_URL, self.author, 'posts/group_list.html'],
            [PROFILE_URL, self.author, 'posts/profile.html'],
            [CREATE_URL, self.author, 'posts/create_post.html'],
            [self.POST_DETAIL_URL, self.author, 'posts/post_detail.html'],
            [self.POST_EDIT_URL, self.author, 'posts/create_post.html'],
            [FOLLOW_INDEX, self.author, 'posts/follow.html'],
            [UNEXISTING_PAGE, self.author, 'core/404.html'],
        ]
        for url, client, template in templates_url:
            with self.subTest(url=url):
                self.assertTemplateUsed(
                    client.get(url),
                    template
                )
