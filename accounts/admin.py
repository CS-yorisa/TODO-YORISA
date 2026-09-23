from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Member, Terms

admin.site.register(Member, UserAdmin)


@admin.register(Terms)
class TermsAdmin(admin.ModelAdmin):
    list_display = ["kind", "version", "title", "is_required", "effective_at"]
    list_filter = ["kind", "is_required"]
