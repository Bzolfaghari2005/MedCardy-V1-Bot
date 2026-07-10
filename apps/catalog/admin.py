from django.contrib import admin
from apps.catalog.models import Category, Lesson


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['title', 'slug', 'parent', 'is_active', 'sort_order', 'created_at']
    list_filter = ['is_active', 'parent']
    search_fields = ['title', 'slug']
    prepopulated_fields = {'slug': ('title',)}
    list_editable = ['is_active', 'sort_order']
    ordering = ['sort_order', 'title']
    list_per_page = 50


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'is_active', 'sort_order', 'created_at']
    list_filter = ['is_active', 'category']
    search_fields = ['title', 'category__title']
    list_editable = ['is_active', 'sort_order']
    ordering = ['sort_order', 'title']
    list_per_page = 50
