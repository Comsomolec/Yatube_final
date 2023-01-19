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
TEST_USERNAME = 'Author_post'
DEFAULT_POSTS_IMG_PATH = 'posts/'
TEST_IMG_NAME = 'small.gif'
TEST_IMAGE = (
    b'\x47\x49\x46\x38\x39\x61\x02\x00'
    b'\x01\x00\x80\x00\x00\x00\x00\x00'
    b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
    b'\x00\x00\x00\x2C\x00\x00\x00\x00'
    b'\x02\x00\x01\x00\x00\x02\x02\x0C'
    b'\x0A\x00\x3B'
)
TEST_IMAGE_TYPE = 'image/gif'

INDEX_URL = reverse('posts:main_page')
CREATE_URL = reverse('posts:post_create')
PROFILE_URL = reverse('posts:profile', args=[TEST_USERNAME])
GROUP_LIST_URL = reverse('posts:group_posts', args=[TEST_SLUG])


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=TEST_USERNAME)
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
        """Создаем и авторизуем пользователя - автор поста"""

        self.author_post_client = Client()
        self.author_post_client.force_login(self.user)

    def test_form_post_create_work_correct(self):
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

    def test_form_post_edit_work_correct(self):
        """Отправка формы при редактирования поста работает корректно."""

        test_image = SimpleUploadedFile(
            TEST_IMG_NAME,
            TEST_IMAGE,
            TEST_IMAGE_TYPE
        )
        data = {
            'text': 'Отредактированный пост',
            'group': self.group2.id,
            'image': test_image
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
        self.assertTrue(post.image)

    def test_form_comment_work_correct(self):
        """Отправка формы добавления комментария работает корректно."""

        self.assertEqual(len(Comment.objects.all()), 0)
        data = {
            'text': 'Тестовый комментарий',
        }
        response = self.author_post_client.post(
            self.COMMENT_URL,
            data,
            follow=True
        )
        self.assertRedirects(response, self.POST_DETAIL_URL)
        comments = self.author_post_client.get(
            self.POST_DETAIL_URL).context['comments']
        self.assertEqual(len(comments), 1)
        comment = comments[0]
        self.assertEqual(comment.text, data['text'])
        self.assertEqual(comment.author, self.post.author)

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
