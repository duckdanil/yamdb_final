import random
from smtplib import SMTPResponseException
from string import ascii_lowercase, ascii_uppercase, digits

from api.filters import TitleFilter
from api.permissions import (AdminOnly, AdminOrModeratorOrAuthorOrReadOnly,
                             AdminOrReadOnly)
from api.serializers import (CategorySerializer, CommentSerializer,
                             GenreSerializer, GettokenSerializer,
                             ReviewSerializer, SignupSerializer,
                             TitleReadSerializer, TitleWriteSerializer,
                             UserSerializer, UserwithlockSerializer)
from django.conf import settings
from django.core.mail import send_mail
from django.db.models import Avg
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.decorators import action, api_view
from rest_framework.filters import SearchFilter
from rest_framework.mixins import (CreateModelMixin, DestroyModelMixin,
                                   ListModelMixin)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet, ModelViewSet
from rest_framework_simplejwt.tokens import RefreshToken

from reviews.models import Category, Genre, Review, Title, User


EMAIL_SUBJECT = 'Сервис YaMDB ждет подтверждания email'
EMAIL_BODY = (
    'Для подтверждения email воспользуйтесь этим кодом: {code}'
)
SEND_EMAIL = 'Код подтверждения отправлен на почту {email}.'
USERNAME_USED = 'Пользователь {username} уже существует!'
EMAIL_USED = 'Почта {email} используется другим пользователем!'
SEND_EMAIL_ERROR = (
    'Не удалось отправь электронное письмо на {email}. '
    'Код ошибки: {code}. Ошибка: {error}.'
)
SEND_EMAIL_ERROR_JSON = (
    'Не удалось отправить электронное письмо на {email}! '
    'Пользователь {username} не создан!'
)
BAD_CONFIRMATION_CODE = 'Не корректный confirmation code: {code}!'


def send_email_with_confirmation_code(
    email, confirmation_code, add_user_flag, username
):
    """
    Сервис YaMDB отправляет письмо с кодом подтверждения
    (confirmation_code) на указанный адрес email.
    """
    try:
        send_mail(
            EMAIL_SUBJECT,
            EMAIL_BODY.format(code=confirmation_code),
            settings.EMAIL_HOST_USER,
            [email, ],
            fail_silently=False,
        )
        if add_user_flag:
            User.objects.create(
                username=username, email=email,
                confirmation_code=confirmation_code
            )
        return Response(
            {'email': email, 'username': username},
            status=status.HTTP_200_OK
        )
    except SMTPResponseException as error:
        print(
            SEND_EMAIL_ERROR.format(
                email=email, code=error.smtp_code, error=error.smtp_error
            )
        )
        return Response(
            {
                'status': SEND_EMAIL_ERROR_JSON.format(
                    email=email, username=username
                )
            },
            status=status.HTTP_400_BAD_REQUEST
        )


def generate_confirmation_code():
    """Генератор кода подтверждения."""
    return (
        ''.join(random.choices(
            ascii_uppercase + digits + ascii_lowercase,
            k=settings.CONFIRMATION_CODE_LENGTH)
        )
    )


class CategoryViewSet(
    CreateModelMixin, ListModelMixin, DestroyModelMixin, GenericViewSet
):
    """Работа с категориями."""

    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = (AdminOrReadOnly,)
    filter_backends = (SearchFilter, )
    search_fields = ('name', )
    lookup_field = 'slug'
    lookup_value_regex = r'[-a-zA-Z0-9_]+'


class GenreViewSet(
    CreateModelMixin, ListModelMixin, DestroyModelMixin, GenericViewSet
):
    """Работа с жанрами."""

    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    permission_classes = (AdminOrReadOnly,)
    filter_backends = (SearchFilter,)
    search_fields = ('name', )
    lookup_field = 'slug'
    lookup_value_regex = r'[-a-zA-Z0-9_]+'


class TitleViewSet(ModelViewSet):
    """Работа с произведениями."""

    queryset = Title.objects.annotate(rating=Avg('reviews__score')).all()
    permission_classes = (AdminOrReadOnly,)
    filter_backends = (DjangoFilterBackend, )
    filterset_class = TitleFilter

    def get_serializer_class(self):
        if self.action == 'list' or self.action == 'retrieve':
            return TitleReadSerializer
        return TitleWriteSerializer


class ReviewViewSet(ModelViewSet):
    """Работа с отзывами."""

    serializer_class = ReviewSerializer
    permission_classes = (AdminOrModeratorOrAuthorOrReadOnly,)

    def get_title(self):
        return Title.objects.get(pk=self.kwargs.get('title_id'))

    def get_queryset(self):
        return self.get_title().reviews.all()

    def perform_create(self, serializer):
        serializer.save(author=self.request.user, title=self.get_title())


class CommentViewSet(ModelViewSet):
    """Работа с комментариями."""

    serializer_class = CommentSerializer
    permission_classes = (AdminOrModeratorOrAuthorOrReadOnly,)

    def get_review(self):
        get_object_or_404(Title, pk=self.kwargs.get('title_id'))
        return get_object_or_404(Review, pk=self.kwargs.get('review_id'))

    def get_queryset(self):
        return self.get_review().comments.all()

    def perform_create(self, serializer):
        serializer.save(author=self.request.user, review=self.get_review())


class UserViewSet(ModelViewSet):
    """Работа с пользователями."""

    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (AdminOnly,)
    filter_backends = (SearchFilter,)
    search_fields = ('username', )
    # Для обработки запросов вида /api/v1/users/Test/
    lookup_field = 'username'
    lookup_value_regex = r'[\w.@+-]+'
    http_method_names = ['get', 'post', 'patch', 'delete']

    @action(
        methods=['GET', 'PATCH'],
        detail=False,
        permission_classes=(IsAuthenticated,),
        url_path='me'
    )
    def get_user_info(self, request):
        """Обработка роута /api/v1/users/me/."""
        if request.method == 'GET':
            serializer = UserwithlockSerializer(request.user)
        if request.method == 'PATCH':
            serializer = UserwithlockSerializer(
                request.user, data=request.data, partial=True
            )
            if not serializer.is_valid():
                return Response(
                    serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
def signup(request):
    """
    Пользователь отправляет POST-запрос на добавление нового пользователя
    с параметрами email и username. Функция отправляет письмо с кодом
    подтверждения (confirmation_code) на адрес email.
    """
    serializer = SignupSerializer(data=request.data)
    if serializer.is_valid():
        username = serializer.validated_data['username']
        email = serializer.validated_data['email']
        user_exist_flag = User.objects.filter(
            username=username, email=email).exists()
        # confirmation_code не задан -> пользователь создан посредством API
        # (роут /api/v1/users/) или панели администрирования
        if (
            user_exist_flag
            and not User.objects.get(username=username).confirmation_code
        ):
            confirmation_code = generate_confirmation_code()
            user = User.objects.get(username=username)
            user.confirmation_code = confirmation_code
            user.save()
            return send_email_with_confirmation_code(
                email, confirmation_code, False, username)
        # confirmation_code задан -> пользователь создан посредством API
        # ранее (роут /api/v1/auth/signup/) или панели администрирования
        elif user_exist_flag:
            confirmation_code = User.objects.get(
                username=username).confirmation_code
            return send_email_with_confirmation_code(
                email, confirmation_code, False, username)
        # confirmation_code не задан -> пользователь создается посредством API
        # впервые (роут /api/v1/auth/signup/)
        else:
            if User.objects.filter(username=username).exists():
                return Response(
                    {'status': USERNAME_USED.format(username=username)},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if User.objects.filter(email=email).exists():
                return Response(
                    {'status': EMAIL_USED.format(email=email)},
                    status=status.HTTP_400_BAD_REQUEST
                )
            confirmation_code = generate_confirmation_code()
            return send_email_with_confirmation_code(
                email, confirmation_code, True, username
            )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def get_token(request):
    """
    Пользователь отправляет POST-запрос с параметрами
    username и confirmation_code на эндпоинт,
    в ответе на запрос ему приходит token (JWT-токен).
    """
    serializer = GettokenSerializer(data=request.data)
    if serializer.is_valid():
        username = serializer.validated_data['username']
        confirmation_code = serializer.validated_data['confirmation_code']
        user = get_object_or_404(User, username=username)
        if not user.confirmation_code == confirmation_code:
            return Response(
                {
                    'status': BAD_CONFIRMATION_CODE.format(
                        code=confirmation_code
                    )
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(
            {
                'access': str(RefreshToken.for_user(user).access_token)
            },
            status=status.HTTP_200_OK
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
