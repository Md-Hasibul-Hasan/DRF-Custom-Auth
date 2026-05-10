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

        ("Security Fields", {'fields': ['failed_login_attempts','locked_until','last_login_ip','otp_attempts','otp_locked_until','last_otp_sent_at']}),

        ("OTP Verification Fields", {'fields': ['otp','otp_created_at','otp_expires_at']}),

        ("Email Change Fields", {'fields': ['pending_email','pending_email_otp','pending_email_otp_created_at','pending_email_otp_expires_at']}),

        ("2FA Fields", {'fields': ['is_2fa_enabled','two_fa_method','two_fa_otp','two_fa_otp_created_at','two_fa_otp_expires_at','two_fa_attempts','two_fa_locked_until']}),
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


@admin.register(LoginHistory)
class LoginHistoryModelAdmin(admin.ModelAdmin):
    model = LoginHistory

    list_display = ('user', 'ip_address', 'user_agent', 'login_time', 'is_successful', 'failure_reason')    

    search_fields = ('user__email', 'ip_address', 'user_agent')


@admin.register(UserSession)
class UserSessionModelAdmin(admin.ModelAdmin):
    model = UserSession

    list_display = ('user', 'ip_address', 'user_agent', 'created_at', 'last_activity', 'is_active')


@admin.register(TwoFALog)
class TwoFALogModelAdmin(admin.ModelAdmin):
    model = TwoFALog

    list_display = ('user', 'action', 'ip_address', 'user_agent', 'status', 'timestamp')    

