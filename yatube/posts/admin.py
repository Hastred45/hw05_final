from django.contrib import admin

from .models import Group, Post, Comment, Follow

admin.site.register(Group)


@admin.register(Comment)
class PostAdmin(admin.ModelAdmin):
    list_display = ('id', 'text', 'author', 'created', 'post')
    search_fields = ('text',)
    list_filter = ('created',)


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('id', 'text', 'pub_date', 'author', 'group', 'image',)
    search_fields = ('text',)
    list_filter = ('pub_date',)
    list_editable = ('group',)
    empty_value_display = '-пусто-'


@admin.register(Follow)
class PostAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'author')
