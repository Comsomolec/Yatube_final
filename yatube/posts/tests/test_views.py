import tempfile
import shutil

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache
from django.test import TestCase, Client, override_settings
from django.urls import reverse

from ..models import Group, Post, User, Follow
from yatube.settings import POSTS_IN_PAGE


TEST_SLUG_GROUP1 = 'test_slug_1'
TEST_SLUG_GROUP2 = 'test_slug_2'
TEST_USERNAME_AUTHOR = 'Author_post'
TEST_USERNAME_ANOTHER = 'Another_user'
TEST_IMAGE = (
    b'\x47\x49\x46\x38\x39\x61\x02\x00'
    b'\x01\x00\x80\x00\x00\x00\x00\x00'
    b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
    b'\x00\x00\x00\x2C\x00\x00\x00\x00'
    b'\x02\x00\x01\x00\x00\x02\x02\x0C'
    b'\x0A\x00\x3B'
)
TEST_COMMENT = 'Тестовый комментарий'

INDEX_URL = reverse('posts:main_page')
CREATE_URL = reverse('posts:post_create')
PROFILE_URL = reverse('posts:profile', args=[TEST_USERNAME_AUTHOR])
GROUP_LIST_URL = reverse('posts:group_posts', args=[TEST_SLUG_GROUP1])
GROUP2_LIST_URL = reverse('posts:group_posts', args=[TEST_SLUG_GROUP2])
FOLLOW_INDEX_URL = reverse('posts:follow_index')
FOLLOW_URL = reverse('posts:profile_follow', args=[TEST_USERNAME_AUTHOR])
UNFOLLOW_URL = reverse('posts:profile_unfollow', args=[TEST_USERNAME_AUTHOR])

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostViewTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=TEST_USERNAME_AUTHOR)
        cls.user_another = User.objects.create_user(
            username=TEST_USERNAME_ANOTHER)
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug=TEST_SLUG_GROUP1,
            description='Тестовое описание',
        )
        cls.group2 = Group.objects.create(
            title='Тестовая группа 2',
            slug=TEST_SLUG_GROUP2,
            description='Пост не должен попасть в эту группу',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
            image=SimpleUploadedFile(
                name='small.gif',
                content=TEST_IMAGE,
                content_type='image/gif'
            )
        )
        cls.POST_DETAIL_URL = reverse(
            'posts:post_detail',
            args=[cls.post.pk]
        )
        cls.POST_EDIT_URL = reverse(
            'posts:post_edit',
            args=[cls.post.pk]
        )
        cls.another_client = Client()
        cls.another_client.force_login(cls.user_another)
        cls.author_post_client = Client()
        cls.author_post_client.force_login(cls.user)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):

        cache.clear()

    def test_pages_formed_with_correct_context(self):
        """Страницы сформированы с правильным контекстом."""

        Follow.objects.create(
            user=self.user_another,
            author=self.user
        )
        urls = [
            INDEX_URL,
            PROFILE_URL,
            GROUP_LIST_URL,
            self.POST_DETAIL_URL,
            FOLLOW_INDEX_URL
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.another_client.get(url)
                if url == self.POST_DETAIL_URL:
                    post = response.context['post']
                else:
                    posts = response.context['page_obj']
                    self.assertEqual(len(posts), 1)
                    post = posts[0]
                self.assertEqual(post.pk, self.post.pk)
                self.assertEqual(post.text, self.post.text)
                self.assertEqual(post.author, self.post.author)
                self.assertEqual(post.group, self.post.group)
                self.assertEqual(post.image, self.post.image)

    def test_post_not_included_in_another_group(self):
        """Пост не попал в другую группу"""

        self.assertNotIn(self.post, self.author_post_client.get(
            GROUP2_LIST_URL).context['page_obj'])

    def test_author_in_context_profile(self):
        """Проверка автора в контексте профиля"""

        self.assertEqual(self.user, self.author_post_client.get(
            PROFILE_URL).context['author'])

    def test_group_in_context_group_list(self):
        """Проверка группы в контексте групп-ленты """

        group = self.author_post_client.get(
            GROUP_LIST_URL).context['group']
        self.assertEqual(self.group, group)
        self.assertEqual(self.group.title, group.title)
        self.assertEqual(self.group.slug, group.slug)
        self.assertEqual(self.group.id, group.id)

    def test_post_not_included_in_another_subscribe_list(self):
        """Пост не попал на чужую ленту-подписок."""

        Follow.objects.create(
            user=self.user_another,
            author=self.user
        )
        self.assertNotIn(self.post, self.author_post_client.get(
            FOLLOW_INDEX_URL).context['page_obj'])

    def test_paginator(self):
        """Тестирование пагинатора"""

        Post.objects.bulk_create(
            Post(text=f'Тестовый пост {i}', author=self.user, group=self.group)
            for i in range(POSTS_IN_PAGE)
        )
        posts_count = len(Post.objects.all())
        last_page_number = (posts_count // POSTS_IN_PAGE) + 1
        post_in_last_page = posts_count % POSTS_IN_PAGE
        Follow.objects.create(
            user=self.user_another,
            author=self.user
        )
        pages = {
            INDEX_URL: POSTS_IN_PAGE,
            PROFILE_URL: POSTS_IN_PAGE,
            GROUP_LIST_URL: POSTS_IN_PAGE,
            FOLLOW_INDEX_URL: POSTS_IN_PAGE,
            INDEX_URL + f'?page={last_page_number}': post_in_last_page,
            PROFILE_URL + f'?page={last_page_number}': post_in_last_page,
            GROUP_LIST_URL + f'?page={last_page_number}': post_in_last_page,
            FOLLOW_INDEX_URL + f'?page={last_page_number}': post_in_last_page,
        }
        for url, amount_posts in pages.items():
            with self.subTest(url=url):
                self.assertEqual(
                    len(self.another_client.get(url).context['page_obj']),
                    amount_posts)

    def test_cache_index(self):
        """Тестирование кэша для main_page."""

        response = self.author_post_client.get(INDEX_URL)
        first_get_content = response.content
        response.context['page_obj'][0].delete()
        second_get_content = self.author_post_client.get(INDEX_URL).content
        self.assertEqual(first_get_content, second_get_content)
        cache.clear()
        third_get_content = self.author_post_client.get(INDEX_URL).content
        self.assertNotEqual(third_get_content, second_get_content)

    def test_follow_user(self):
        """Тестирование подписки на пользователя"""

        self.assertFalse(
            Follow.objects.filter(
                user=self.user_another, author=self.user).exists()
        )
        self.another_client.get(FOLLOW_URL)
        self.assertTrue(
            Follow.objects.filter(
                user=self.user_another, author=self.user).exists()
        )

    def test_unfollow_user(self):
        """Тестирование отписки от пользователя"""

        self.another_client.get(UNFOLLOW_URL)
        self.assertFalse(
            Follow.objects.filter(
                user=self.user_another, author=self.user).exists()
        )
