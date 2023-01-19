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
        cls.COMMENT_URL = reverse(
            'posts:add_comment',
            args=[cls.post.pk]
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        """Создаем и авторизуем пользователя."""

        self.another_client = Client()
        self.another_client.force_login(self.user_another)
        self.author_post_client = Client()
        self.author_post_client.force_login(self.user)

        cache.clear()

    def test_pages_formed_with_correct_context(self):
        """Страницы сформированы с правильным контекстом."""

        data = {
            'text': TEST_COMMENT,
        }
        self.author_post_client.post(
            self.COMMENT_URL,
            data,
            follow=True
        )
        urls = [
            INDEX_URL,
            PROFILE_URL,
            GROUP_LIST_URL,
            self.POST_DETAIL_URL,
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.author_post_client.get(url)
                if url == self.POST_DETAIL_URL:
                    post = response.context['post']
                    comments = response.context['comments']
                    self.assertEqual(len(comments), 1)
                    comment = comments[0]
                    self.assertEqual(comment.post.id, self.post.pk)
                    self.assertEqual(comment.text, TEST_COMMENT)
                    self.assertEqual(comment.author, self.post.author)
                else:
                    posts = response.context['page_obj']
                    self.assertEqual(len(posts), 1)
                    post = posts[0]
                self.assertEqual(post.pk, self.post.pk)
                self.assertEqual(post.text, self.post.text)
                self.assertEqual(post.author, self.post.author)
                self.assertEqual(post.group, self.post.group)
                self.assertTrue(post.image)

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

    def test_paginator(self):
        """Тестирование пагинатора"""
        posts_in_second_page = len(Post.objects.all())

        Post.objects.bulk_create(
            Post(text=f'Тестовый пост {i}', author=self.user, group=self.group)
            for i in range(POSTS_IN_PAGE)
        )
        pages = {
            INDEX_URL: POSTS_IN_PAGE,
            PROFILE_URL: POSTS_IN_PAGE,
            GROUP_LIST_URL: POSTS_IN_PAGE,
            INDEX_URL + '?page=2': posts_in_second_page,
            PROFILE_URL + '?page=2': posts_in_second_page,
            GROUP_LIST_URL + '?page=2': posts_in_second_page,
        }
        for page, amount_posts in pages.items():
            with self.subTest(page=page):
                self.assertEqual(
                    len(self.author_post_client.get(page).context['page_obj']),
                    amount_posts)

    def test_cache_index(self):
        """Тестирование кэша для main_page."""

        post = Post.objects.create(
            author=self.user,
            text='Этот пост будет удален',
            group=self.group,
        )
        first_time_get_posts = self.author_post_client.get(INDEX_URL).content
        Post.objects.filter(id=post.pk).delete()
        second_time_get_posts = self.author_post_client.get(INDEX_URL).content
        self.assertEqual(first_time_get_posts, second_time_get_posts)
        cache.clear()
        third_time_get_posts = self.author_post_client.get(INDEX_URL).content
        self.assertNotEqual(third_time_get_posts, second_time_get_posts)

    def test_follow_user(self):
        """Тестирование подписки на пользователей"""

        self.assertFalse(
            Follow.objects.filter(user=self.user_another, author=self.user)
        )
        self.another_client.get(FOLLOW_URL)
        self.assertTrue(
            Follow.objects.filter(user=self.user_another, author=self.user)
        )
        posts = self.another_client.get(FOLLOW_INDEX_URL).context['page_obj']
        self.assertEqual(len(posts), 1)
        data = {
            'text': 'Пост отображается у подписчиков',
            'group': self.group.id,
        }
        self.author_post_client.post(CREATE_URL, data=data)
        posts = self.another_client.get(FOLLOW_INDEX_URL).context['page_obj']
        self.assertEqual(len(posts), 2)
        post = posts[0]
        self.assertEqual(post.text, data['text'])
        self.assertEqual(post.group.id, data['group'])
        self.assertEqual(post.author, self.user)
        self.another_client.get(UNFOLLOW_URL)
        posts = self.another_client.get(FOLLOW_INDEX_URL).context['page_obj']
        self.assertEqual(len(posts), 0)
