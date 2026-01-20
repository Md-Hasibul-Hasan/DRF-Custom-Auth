from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import *
from django.utils.html import format_html


# Register your models here.
@admin.register(User)
class UserModelAdmin(BaseUserAdmin):
    model = User
    # The fields to be used in displaying the User model.
    # These override the definitions on the base UserAdmin
    # that reference specific fields on auth.User.
    list_display = ('id','email', 'name', 'image_preview', 'is_active', 'is_staff','is_superuser',)
    list_display_links = ('id','email', 'name')
    list_filter = ('is_active','is_staff','is_superuser',)
    fieldsets = [
        ("User Details", {'fields': ['email', 'password']}),

        ("Personal Details", {'fields': ['name','image']}),
        
        ("Permissions", {'fields': ['is_active','is_staff','is_superuser','groups','user_permissions']}),
    ]

    add_fieldsets = [
        (
        None,
        {
            'classes': ('wide',),
            'fields': ('name','email','password1', 'password2'),
        },
        ),
    ]

    search_fields = ('email',)
    ordering = ('email','id',)
    filter_horizontal = ('groups','user_permissions')

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="width:40px;height:40px;object-fit:cover;border-radius:50%;" />',
                obj.image.url
            )
        return "No Image"

    image_preview.short_description = "Profile"


