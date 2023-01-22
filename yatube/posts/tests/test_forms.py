import shutil

from django import forms
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client, override_settings
from django.urls import reverse

from ..models import Post, Group, User, Comment
from django.conf import settings
import tempfile


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

TEST_SLUG = 'test_slug'
TEST2_SLUG = 'test2_slug'
TEST_USERNAME_AUTHOR = 'Author_post'
TEST_USERNAME_ANOTHER = 'Another'
DEFAULT_POSTS_IMG_PATH = 'posts/'
TEST_IMG_NAME = 'small.gif'
TEST_IMG_NAME_2 = 'big.gif'
TEST_IMAGE = (
    b'\x47\x49\x46\x38\x39\x61\x02\x00'
    b'\x01\x00\x80\x00\x00\x00\x00\x00'
    b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
    b'\x00\x00\x00\x2C\x00\x00\x00\x00'
    b'\x02\x00\x01\x00\x00\x02\x02\x0C'
    b'\x0A\x00\x3B'
)
TEST_IMAGE_2 = (
    b'\x47\x49\x46\x38\x39\x61\x02\x00'
    b'\x01\x00\x80\x00\x00\x00\x00\x00'
    b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
    b'\x00\x00\x00\x2C\x00\x00\x00\x00'
    b'\x02\x00\x01\x00\x00\x02\x02\x0C'
    b'\x0A\x00\x3B'
)
TEST_IMAGE_TYPE = 'image/gif'
TEST_IMAGE_TYPE_2 = 'image/gif'

INDEX_URL = reverse('posts:main_page')
CREATE_URL = reverse('posts:post_create')
PROFILE_URL = reverse('posts:profile', args=[TEST_USERNAME_AUTHOR])
GROUP_LIST_URL = reverse('posts:group_posts', args=[TEST_SLUG])
LOGIN = reverse('users:login')


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=TEST_USERNAME_AUTHOR)
        cls.user_another = User.objects.create_user(
            username=TEST_USERNAME_ANOTHER)
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug=TEST_SLUG,
            description='Тестовое описание',
        )
        cls.group2 = Group.objects.create(
            title='Тестовая группа',
            slug=TEST2_SLUG,
            description='Группа для проверки редактирования',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Пост для проверки редактирования',
            group=cls.group,
            image=SimpleUploadedFile(
                TEST_IMG_NAME,
                TEST_IMAGE,
                TEST_IMAGE_TYPE
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
        cls.EDIT_REDIRECT_LOGIN = f'{LOGIN}?next={cls.POST_EDIT_URL}'
        cls.guest = Client()
        cls.another_client = Client()
        cls.another_client.force_login(cls.user_another)
        cls.author_post_client = Client()
        cls.author_post_client.force_login(cls.user)

    def tearDown(self):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_form_post_create(self):
        """Отправка формы при создании поста работает корректно."""
        test_image = SimpleUploadedFile(
            TEST_IMG_NAME,
            TEST_IMAGE,
            TEST_IMAGE_TYPE
        )
        posts = set(Post.objects.all())
        data = {
            'text': 'Текст нового поста',
            'group': self.group.id,
            'image': test_image,
        }
        response = self.author_post_client.post(
            CREATE_URL,
            data=data,
            follow=True
        )
        self.assertRedirects(response, PROFILE_URL)
        posts = set(Post.objects.all()) - posts
        self.assertEqual(len(posts), 1)
        post = posts.pop()
        self.assertEqual(post.text, data['text'])
        self.assertEqual(post.group.id, data['group'])
        self.assertEqual(post.author, self.user)
        self.assertTrue(post.image)

    def test_form_post_edit(self):
        """Отправка формы при редактирования поста работает корректно."""

        new_image = SimpleUploadedFile(
            TEST_IMG_NAME_2,
            TEST_IMAGE_2,
            TEST_IMAGE_TYPE_2
        )
        data = {
            'text': 'Отредактированный пост',
            'group': self.group2.id,
            'image': new_image
        }
        response = self.author_post_client.post(
            self.POST_EDIT_URL,
            data,
            follow=True
        )
        self.assertRedirects(response, self.POST_DETAIL_URL)
        post = Post.objects.get(id=self.post.id)
        self.assertEqual(post.text, data['text'])
        self.assertEqual(post.group.id, data['group'])
        self.assertEqual(post.author, self.post.author)
        self.assertEqual(
            post.image.name, Post.image.field.upload_to + data['image'].name
        )

    def test_form_comment(self):
        """Отправка формы добавления комментария работает корректно."""
        comments = set(Comment.objects.all())
        data = {
            'text': 'Тестовый комментарий',
        }
        response = self.another_client.post(
            self.COMMENT_URL,
            data,
            follow=True
        )
        self.assertRedirects(response, self.POST_DETAIL_URL)
        comments = set(Comment.objects.all()) - comments
        self.assertEqual(len(comments), 1)
        comment = comments.pop()
        self.assertEqual(comment.text, data['text'])
        self.assertEqual(comment.author, self.user_another)
        self.assertEqual(comment.post, self.post)

    def test_another_user_try_edit_post(self):
        """Другой пользователь пытается отредактировать пост."""

        clients = [
            [self.another_client, self.POST_DETAIL_URL],
            [self.guest, self.EDIT_REDIRECT_LOGIN]
        ]
        new_image = SimpleUploadedFile(
            TEST_IMG_NAME_2,
            TEST_IMAGE_2,
            TEST_IMAGE_TYPE_2
        )
        data = {
            'text': 'Отредактированный пост',
            'group': self.group2.id,
            'image': new_image
        }
        for client, redirect in clients:
            with self.subTest(client=client):
                response = client.post(self.POST_EDIT_URL, data, follow=True)
                post = Post.objects.get(id=self.post.id)
                self.assertEqual(post.author, self.post.author)
                self.assertEqual(post.text, self.post.text)
                self.assertEqual(post.group, self.post.group)
                self.assertEqual(post.image, self.post.image)
                self.assertRedirects(response, redirect)

    def test_guest_user_try_create_post(self):
        """Гостевой пользователь пытается создать пост"""

        posts_before = set(Post.objects.all())
        test_image = SimpleUploadedFile(
            TEST_IMG_NAME,
            TEST_IMAGE,
            TEST_IMAGE_TYPE
        )
        data = {
            'text': 'Текст другого поста',
            'group': self.group.id,
            'image': test_image,
        }
        self.guest.post(
            CREATE_URL,
            data=data,
            follow=True
        )
        posts_after = set(Post.objects.all())
        self.assertEqual(posts_before, posts_after)

    def test_guest_user_try_create_comment(self):
        """Гостевой пользователь пытается создать комментарий"""

        comments_before = set(Comment.objects.all())
        data = {
            'text': 'Тестовый комментарий',
        }
        self.guest.post(
            self.COMMENT_URL,
            data,
            follow=True
        )
        comments_after = set(Comment.objects.all())
        self.assertEqual(comments_before, comments_after)

    def test_post_create_and_edit_show_correct_context(self):
        """Шаблоны create и post_edit сформированы с правильным контекстом."""

        urls_list = [
            CREATE_URL,
            self.POST_EDIT_URL,
        ]
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.ModelChoiceField,
            'image': forms.ImageField
        }
        for url in urls_list:
            with self.subTest(url=url):
                response = self.author_post_client.get(url)
                for value, expected in form_fields.items():
                    self.assertIsInstance(
                        response.context['form'].fields[value],
                        expected
                    )

    def test_comment_form_show_correct_context(self):
        """Шаблон comment сформирован с правильным контекстом."""

        self.assertIsInstance(
            self.author_post_client.get(
                self.POST_DETAIL_URL).context['form'].fields['text'],
            forms.fields.CharField
        )
