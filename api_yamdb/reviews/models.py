import datetime as dt

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

LENGTH_TEXT = 15
MAX_LENGTH_TEXT = 256
MAX_LENGTH_SLUG = 50
ADMIN = 'admin'
USER = 'user'
MODERATOR = 'moderator'
ROLE = [
    (USER, 'Пользователь'),
    (MODERATOR, 'Модератор'),
    (ADMIN, 'Администратор')
]


class User(AbstractUser):
    """Кастомная модель пользователя."""

    email = models.EmailField(
        max_length=settings.MAX_LENGTH_EMAIL, unique=True
    )
    bio = models.TextField(
        'Биография',
        blank=True,
    )
    role = models.CharField(
        'Роль',
        choices=ROLE,
        default=USER,
        max_length=9
    )
    confirmation_code = models.CharField(
        'Код подтверждения для API',
        blank=True,
        max_length=settings.CONFIRMATION_CODE_LENGTH
    )

    @property
    def is_admin(self):
        return self.role == ADMIN or self.is_superuser

    @property
    def is_moderator(self):
        return self.role == MODERATOR

    @property
    def is_user(self):
        return self.role == USER


class CategoryGenreCummonModel(models.Model):
    """
    Абстрактная модель.
    Добавляет общие атрибуты для категорий и жанров.
    """

    name = models.CharField(
        'Наименование',
        max_length=MAX_LENGTH_TEXT,
        help_text='Введите наименование'
    )
    slug = models.SlugField(
        'Уникальный slug',
        unique=True,
        max_length=MAX_LENGTH_SLUG,
        help_text='Введите уникальный идентификатор'
    )

    class Meta:
        abstract = True
        ordering = ('slug',)

    def __str__(self):
        return f'{self.slug[0:LENGTH_TEXT]} {self.name[0:LENGTH_TEXT]}'


class ReviewCommentCummonModel(models.Model):
    """
    Абстрактная модель.
    Добавляет общие атрибуты для отзывов и комментариев.
    """

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='%(class)ss',
        verbose_name='Автор',
        help_text='Укажите автора')
    pub_date = models.DateTimeField(
        'Дата публикации',
        auto_now_add=True
    )
    text = models.TextField(
        'Текст',
        help_text='Введите текст'
    )

    class Meta:
        abstract = True
        ordering = ('-pub_date',)

    def __str__(self):
        return (
            f'{self.pk}, {self.text[0:LENGTH_TEXT]}..., '
            f'{self.pub_date.strftime("%Y/%m/%d %H:%M:%S")}, '
            f'{self.author.username}'
        )


class Category(CategoryGenreCummonModel):
    """Категории (типы) произведений."""

    class Meta:
        verbose_name = 'категорию'
        verbose_name_plural = 'Категории'


class Genre(CategoryGenreCummonModel):
    """Категории жанров."""

    class Meta:
        verbose_name = 'жанры'
        verbose_name_plural = 'Жанры'


class Title(models.Model):
    """Произведения, к которым пишут отзывы."""

    name = models.CharField(
        'Наименование',
        max_length=MAX_LENGTH_TEXT,
        help_text='Введите наименование произведения'
    )
    year = models.IntegerField(
        validators=[
            MinValueValidator(
                settings.MIN_YEAR_TITLE,
                settings.SMALL_YEAR_MESSAGE
            ),
            MaxValueValidator(
                int(dt.datetime.now().strftime('%Y')),
                settings.BIG_YEAR_MESSAGE
            )
        ],
        verbose_name='Год',
        help_text='Введите год, в котором было издано произведение'
    )
    description = models.TextField(
        'Описание',
        blank=True,
        null=True,
        help_text='Введите описание произведения'
    )
    category = models.ForeignKey(
        Category,
        null=True,
        on_delete=models.SET_NULL,
        related_name='titles',
        verbose_name='Категория',
        help_text='Введите категорию, к которой будет относиться произведение'
    )
    genre = models.ManyToManyField(
        Genre,
        through='GenreTitle',
        null=True,
        related_name='genres',
        verbose_name='Жанр',
        help_text='Введите жанр, к которому будет относиться произведение'
    )

    class Meta:
        verbose_name = 'произведение'
        verbose_name_plural = 'Произведения'
        ordering = ('name',)

    def __str__(self):
        return (
            f'{self.name[0:LENGTH_TEXT]} {self.year} '
            f'{self.description[0:LENGTH_TEXT]} '
            f'{self.category} {self.genre}'
        )


class GenreTitle(models.Model):
    """
    Одно произведение может быть привязано к нескольким жанрам.
    В этой модели будут связаны id жанров и id произведений.
    """

    title = models.ForeignKey(
        Title,
        on_delete=models.CASCADE,
        verbose_name="Произведение",
        help_text='Введите ID произведения'
    )
    genre = models.ForeignKey(
        Genre,
        on_delete=models.CASCADE,
        verbose_name="Жанр",
        help_text='Введите ID жанра'
    )

    class Meta:
        verbose_name = "произведению нужные жанры"
        verbose_name_plural = "Произведения и жанры"
        ordering = ('genre',)

    def __str__(self):
        return f'{self.title} {self.genre}'


class Review(ReviewCommentCummonModel):
    """Отзывы на произведения."""

    title = models.ForeignKey(
        Title,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name="Произведение",
        help_text='Укажите произведение, к которому будет относиться отзыв'
    )
    score = models.IntegerField(
        validators=[
            MinValueValidator(
                settings.MIN_SCORE, settings.MIN_SCORE_MESSAGE
            ),
            MaxValueValidator(
                settings.MAX_SCORE, settings.MAX_SCORE_MESSAGE
            )
        ],
        verbose_name='Оценка',
        help_text='Введите оценку произведения'
    )

    class Meta:
        verbose_name = "отзыв"
        verbose_name_plural = "Отзывы к произведениям"
        constraints = [
            models.UniqueConstraint(
                fields=['author', 'title'], name='unique_review')
        ]


class Comment(ReviewCommentCummonModel):
    """Комментарии к отзывам."""

    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,
        blank=True,
        related_name='comments',
        verbose_name="Отзыв",
        help_text='Укажите отзыв, к которому будет относиться комментарий'
    )

    class Meta:
        verbose_name = "комментарий"
        verbose_name_plural = "Комментарии к отзывам"
