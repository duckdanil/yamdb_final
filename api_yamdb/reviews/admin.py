from django.contrib import admin

from reviews.models import (Category, Comment, Genre, GenreTitle, Review,
                            Title, User)


class CategoryGenreAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'name',
        'slug'
    )
    list_editable = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name', 'slug')


@admin.register(Category)
class CategoryAdmin(CategoryGenreAdmin):
    ...


@admin.register(Genre)
class GenreAdmin(CategoryGenreAdmin):
    ...


@admin.register(Title)
class TitleAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'name',
        'year',
        'description',
        'category'
    )
    list_editable = ('name', 'year', 'description', 'category')
    search_fields = ('name',)


@admin.register(GenreTitle)
class GenreTitleAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'genre',
        'title'
    )
    list_editable = ('genre', 'title')
    search_fields = ('genre', 'title')


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'author',
        'pub_date',
        'title',
        'text',
        'score'
    )
    list_editable = ('author', 'title', 'text', 'score')
    search_fields = ('author', 'title')


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'author',
        'pub_date',
        'review',
        'text',
    )
    list_editable = ('author', 'review', 'text')
    search_fields = ('text', 'author__username')


admin.site.register(User)
