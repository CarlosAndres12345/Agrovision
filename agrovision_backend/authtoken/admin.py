from django.contrib import admin
from .models import Token


@admin.register(Token)
class TokenAdmin(admin.ModelAdmin):
    list_display = ("user", "token", "created_at")
    list_filter = ("created_at",)
    search_fields = ("user__username", "token")
    readonly_fields = ("token", "created_at")

    def has_add_permission(self, request):
        return False
