from django.contrib import admin
from apps.favorites.models import Favorite


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ['user', 'object_type', 'object_id', 'title_snapshot', 'created_at']
    list_filter = ['object_type', 'created_at']
    search_fields = ['user__user_code', 'user__username', 'title_snapshot']
    readonly_fields = ['created_at']
    list_per_page = 50
