import csv

from django.core.management.base import BaseCommand

from reviews.models import (Category, Comment, Genre, GenreTitle, Review,
                            Title, User)


HELP_MESSAGE = 'Импорт данных из static/data/*.csv'
START_MESSAGE = 'Начинаем импорт...'
STOP_MESSAGE = 'Импорт закончен...'
IMPORT_ERROR = 'Что-то пошло не так: {error}.'
IMPORT_MESSAGE = 'Обрабатывается набор данных: {data}'
PATH_TO_CSV_FILES = 'api_yamdb/static/data/'
CATEGORY_FILE = f'{PATH_TO_CSV_FILES}category.csv'
COMMENT_FILE = f'{PATH_TO_CSV_FILES}comments.csv'
GENRE_TITLE_FILE = f'{PATH_TO_CSV_FILES}genre_title.csv'
GENRE_FILE = f'{PATH_TO_CSV_FILES}genre.csv'
REVIEW_FILE = f'{PATH_TO_CSV_FILES}review.csv'
TITLE_FILE = f'{PATH_TO_CSV_FILES}titles.csv'
USER_FILE = f'{PATH_TO_CSV_FILES}users.csv'


def import_to_user(row):
    """Импорт информации из csv файла в модель User."""
    id, username, email, role, bio, first_name, last_name = row
    User.objects.get_or_create(
        username=username, email=email, role=role, bio=bio,
        first_name=first_name, last_name=last_name
    )


def import_to_category(row):
    """Импорт информации из csv файла в модель Category."""
    id, name, slug = row
    Category.objects.get_or_create(id=id, name=name, slug=slug)


def import_to_genre(row):
    """Импорт информации из csv файла в модель Genre."""
    id, name, slug = row
    Genre.objects.get_or_create(id=id, name=name, slug=slug)


def import_to_title(row):
    """Импорт информации из csv файла в модель Title."""
    id, name, year, category_id = row
    category = Category.objects.get(id=category_id)
    Title.objects.get_or_create(id=id, name=name, year=year, category=category)


def import_to_genre_title(row):
    """Импорт информации из csv файла в модель GenreTitle."""
    id, title_id, genre_id = row
    GenreTitle.objects.get_or_create(
        id=id, title_id=title_id, genre_id=genre_id)


def import_to_review(row):
    """Импорт информации из csv файла в модель Review."""
    id, title_id, text, author_id, score, pub_date = row
    author = User.objects.get(id=author_id)
    if not Review.objects.filter(
        id=id, title_id=title_id, author=author
    ).exists():
        review = Review.objects.create(
            id=id, title_id=title_id, text=text, author=author, score=score)
        review.save()
        review.pub_date = pub_date
        review.save()


def import_to_comment(row):
    """Импорт информации из csv файла в модель Comment."""
    id, review_id, text, author_id, pub_date = row
    author = User.objects.get(id=author_id)
    if not Comment.objects.filter(
        id=id, review_id=review_id, text=text, author=author
    ).exists():
        comment = Comment.objects.create(
            id=id, review_id=review_id, text=text, author=author)
        comment.save()
        comment.pub_date = pub_date
        comment.save()


def import_to_model(csv_file):
    """Импорт информации из csv файла в модели."""
    with open(csv_file, encoding='utf-8') as file:
        reader = csv.reader(file)
        # Пропускаем заголовки
        next(reader)
        for row in reader:
            print(IMPORT_MESSAGE.format(data=row))
            if csv_file == USER_FILE:
                import_to_user(row)
            elif csv_file == CATEGORY_FILE:
                import_to_category(row)
            elif csv_file == GENRE_FILE:
                import_to_genre(row)
            elif csv_file == TITLE_FILE:
                import_to_title(row)
            elif csv_file == GENRE_TITLE_FILE:
                import_to_genre_title(row)
            elif csv_file == REVIEW_FILE:
                import_to_review(row)
            elif csv_file == COMMENT_FILE:
                import_to_comment(row)


class Command(BaseCommand):
    """
    Класс для работы managment комманды.
    python api_yamdb/manage.py import_into_db
    """

    help = HELP_MESSAGE

    def handle(self, *args, **options):
        print(START_MESSAGE)
        try:
            import_to_model(USER_FILE)
            import_to_model(CATEGORY_FILE)
            import_to_model(GENRE_FILE)
            import_to_model(TITLE_FILE)
            import_to_model(GENRE_TITLE_FILE)
            import_to_model(REVIEW_FILE)
            import_to_model(COMMENT_FILE)
        except Exception as error:
            print(IMPORT_ERROR.format(error=error))

        finally:
            print(STOP_MESSAGE)
