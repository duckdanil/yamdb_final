import datetime as dt

from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework.serializers import (CharField, EmailField, IntegerField,
                                        ModelSerializer, RegexField,
                                        Serializer, SlugRelatedField,
                                        ValidationError)
from reviews.models import Category, Comment, Genre, Review, Title, User

REVIEW_EXIST = 'Можно оставить только один отзыв на произведение!'
TITLE_EXIST = 'Указанное произведение уже существует в базе данных!'
BAD_USERNAME = 'Нельзя использовать в качестве username {username}!'
MIN_YEAR_ERROR = (
    'Год не может быть меньше {min_year}! Ваше значение: {year}.'
)
MAX_YEAR_ERROR = (
    'Год не может быть больше {max_year}! Ваше значение: {year}.'
)
MIN_SCORE_ERROR = (
    'Оценка не может быть меньше {min_score}! Ваша оценка: {score}.'
)
MAX_SCORE_ERROR = (
    'Оценка не может быть больше {max_score}! Ваша оценка: {score}.'
)


class CategoryGenreCummonSerializer(ModelSerializer):
    """Сериализатор для моделей Category и Genre."""

    ...


class CategorySerializer(CategoryGenreCummonSerializer):
    """Сериализатор для модели Category."""

    class Meta:
        model = Category
        exclude = ('id',)
        lookup_field = 'slug'


class GenreSerializer(CategoryGenreCummonSerializer):
    """Сериализатор для модели Genre."""

    class Meta:
        model = Genre
        exclude = ('id',)


class TitleBaseSerializer(ModelSerializer):
    """Базовый сериализатор для модели Title."""

    category = SlugRelatedField(
        queryset=Category.objects.all(), slug_field='slug')
    genre = SlugRelatedField(
        queryset=Genre.objects.all(), slug_field="slug", many=True)

    class Meta:
        model = Title
        fields = '__all__'


class TitleReadSerializer(TitleBaseSerializer):
    """
    Сериализатор для модели Title.
    GET запросы, т.е. action == 'list'
    """
    category = CategorySerializer(read_only=True)
    genre = GenreSerializer(many=True, required=False, read_only=True)
    rating = IntegerField()


class TitleWriteSerializer(TitleBaseSerializer):
    """
    Сериализатор для модели Title.
    Другие запросы, т.е. action == 'retrieve'
    """

    def validate_year(self, value):
        if value < settings.MIN_YEAR_TITLE:
            raise ValidationError(MIN_YEAR_ERROR.format(
                min_year=settings.MIN_YEAR_TITLE, year=value)
            )
        current_year = int(dt.datetime.now().strftime('%Y'))
        if value > current_year:
            raise ValidationError(MAX_YEAR_ERROR.format(
                max_year=current_year, year=value)
            )
        return value

    def validate(self, data):
        if Title.objects.filter(
                name=data.get('name'),
                year=data.get('year'),
                category_id=data.get('category').id
        ).exists():
            raise ValidationError(TITLE_EXIST)
        return data


class ReviewSerializer(ModelSerializer):
    """Сериализатор для модели Review."""

    author = SlugRelatedField(read_only=True, slug_field='username')

    class Meta:
        model = Review
        fields = '__all__'
        read_only_fields = ('title',)

    def validate(self, data):
        request = self.context.get('request')
        title = get_object_or_404(
            Title, pk=self.context.get('view').kwargs.get('title_id')
        )
        if (
            request.method == 'POST'
            and Review.objects.filter(
                title=title.id, author=request.user).exists()
        ):
            raise ValidationError(REVIEW_EXIST)
        return data


class CommentSerializer(ModelSerializer):
    """Сериализатор для модели Comment."""

    author = SlugRelatedField(read_only=True, slug_field='username')

    class Meta:
        model = Comment
        fields = '__all__'


class UserSerializer(ModelSerializer):
    """Сериализатор для модели User."""

    class Meta:
        model = User
        fields = (
            'username', 'email', 'first_name', 'last_name', 'bio', 'role'
        )


class UserwithlockSerializer(ModelSerializer):
    """Сериализатор для модели User. Запрещено изменение роли."""

    class Meta:
        model = User
        fields = (
            'username', 'email', 'first_name', 'last_name', 'bio', 'role'
        )
        read_only_fields = ('role',)


class SignupSerializer(Serializer):
    """Сериализатор для функции Signup."""

    username = RegexField(
        r'^[\w.@+-]+',
        max_length=settings.MAX_LENGTH_USERNAME,
        min_length=None, allow_blank=False)
    email = EmailField(
        required=True, max_length=settings.MAX_LENGTH_EMAIL)

    def validate_username(self, value):
        if value.lower() == 'me':
            raise ValidationError(BAD_USERNAME.format(username=value))
        return value


class GettokenSerializer(Serializer):
    """Сериализатор для функции get_token."""

    username = CharField(
        required=True, max_length=settings.MAX_LENGTH_USERNAME)
    confirmation_code = CharField(
        required=True, max_length=settings.CONFIRMATION_CODE_LENGTH
    )
