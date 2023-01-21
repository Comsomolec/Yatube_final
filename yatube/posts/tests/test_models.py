from django.test import TestCase

from ..models import Group, Post, User, Comment, Follow

TEST_SLUG = 'test_slug'
TEST_USERNAME_AUTHOR = 'Author_post'
TEST_USERNAME_ANOTHER = 'Another'


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=TEST_USERNAME_AUTHOR)
        cls.another_user = User.objects.create_user(
            username=TEST_USERNAME_ANOTHER)
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug=TEST_SLUG,
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user,
            text='Тестовый комментарий'
        )
        cls.follow = Follow.objects.create(
            user=cls.user,
            author=cls.another_user
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""

        self.assertEqual(self.group.title, str(self.group))
        self.assertEqual(Post.PATTERN.format(
            author=self.post.author.username,
            group=self.post.group.title,
            date=self.post.pub_date,
            text=self.post.text),
            str(self.post)
        )
        self.assertEqual(Comment.PATTERN.format(
            post=self.comment.post.id,
            author=self.comment.author.username,
            date=self.comment.created,
            text=self.comment.text),
            str(self.comment)
        )
        self.assertEqual(Follow.PATTERN.format(
            user=self.follow.user,
            author=self.follow.author),
            str(self.follow)
        )

    def test_post_verbose_names(self):
        """verbose_name модели Post в полях совпадает с ожидаемым."""
        field_verboses = {
            'text': 'Новый пост',
            'pub_date': 'Дата публикации',
            'author': 'Автор',
            'group': 'Группа',
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    Post._meta.get_field(field).verbose_name, expected_value)

    def test_post_help_text(self):
        """help_text модели Post в полях совпадает с ожидаемым."""
        field_help_text = {
            'text': 'Текст нового поста',
            'group': 'Группа, к которой относится пост',
        }
        for field, expected_value in field_help_text.items():
            with self.subTest(field=field):
                self.assertEqual(
                    Post._meta.get_field(field).help_text, expected_value)
