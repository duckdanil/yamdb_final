# yamdb_final
yamdb_final
[![Django-app workflow](https://github.com/duckdanil/yamdb_final/actions/workflows/yamdb_workflow.yml/badge.svg)](https://github.com/duckdanil/yamdb_final/actions/workflows/yamdb_workflow.yml)

REST API проект для сервиса YaMDb — сбор отзывов о фильмах, книгах или музыке.

## Описание

Проект YaMDb собирает отзывы пользователей на произведения.
Произведения делятся на категории: «Книги», «Фильмы», «Музыка».
Список категорий  может быть расширен (например, можно добавить категорию «Изобразительное искусство» или «Ювелирка»).
### Как запустить проект:

Все описанное ниже относится к ОС Linux.
Клонируем репозиторий и переходим в него:
```bash
git clone https://github.com/duckdanil/yamdb_final
cd infra_sp2
cd api_yamdb
```

Создаем и активируем виртуальное окружение:
```bash
python3 -m venv venv
source /venv/bin/activate (source venv/Scripts/activate - для Windows)
python -m pip install --upgrade pip
```

Ставим зависимости из requirements.txt:
```bash
pip install -r requirements.txt
```

Переходим в папку с файлом docker-compose.yaml:
```bash
cd infra
```

Поднимаем контейнеры (infra_db_1, infra_web_1, infra_nginx_1):
```bash
docker-compose up -d --build
```

Выполняем миграции:
```bash
docker-compose exec web python manage.py makemigrations reviews
```
```bash
docker-compose exec web python manage.py migrate
```

Создаем суперпользователя:
```bash
docker-compose exec web python manage.py createsuperuser
```

Србираем статику:
```bash
docker-compose exec web python manage.py collectstatic --no-input
```

Создаем дамп базы данных (нет в текущем репозитории):
```bash
docker-compose exec web python manage.py dumpdata > dumpPostrgeSQL.json
```

Останавливаем контейнеры:
```bash
docker-compose down -v
```


### Документация API YaMDb
Документация доступна по эндпойнту: http://158.160.34.105/redoc/
API доступен по адресу : http://158.160.34.105/api/v1/