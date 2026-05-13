from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .models import LoginHistory, TwoFALog, User, UserSession
from .utils import logout_all_user_sessions


@admin.register(User)
class UserModelAdmin(BaseUserAdmin):
    model = User

    list_display = (
        'id',
        'email',
        'name',
        'image_preview',
        'is_active',
        'is_staff',
        'is_superuser',
        'is_2fa_enabled',
        'account_lock_status',
        'last_login_ip',
        'created_at',
    )
    list_display_links = ('id', 'email', 'name')
    list_filter = (
        'is_active',
        'is_staff',
        'is_superuser',
        'is_2fa_enabled',
        'two_fa_method',
        'created_at',
        'updated_at',
    )
    search_fields = ('email', 'name', 'last_login_ip')
    ordering = ('email', 'id')
    filter_horizontal = ('groups', 'user_permissions')
    readonly_fields = (
        'image_preview',
        'last_login',
        'created_at',
        'updated_at',
        'last_login_ip',
        'failed_login_attempts',
        'locked_until',
        'otp',
        'otp_created_at',
        'otp_expires_at',
        'otp_attempts',
        'otp_locked_until',
        'password_reset_otp',
        'password_reset_otp_created_at',
        'password_reset_otp_expires_at',
        'password_reset_otp_attempts',
        'password_reset_otp_locked_until',
        'pending_email',
        'pending_email_otp',
        'pending_email_otp_created_at',
        'pending_email_otp_expires_at',
        'pending_email_otp_attempts',
        'pending_email_otp_locked_until',
        'two_fa_otp',
        'two_fa_otp_created_at',
        'two_fa_otp_expires_at',
        'two_fa_attempts',
        'two_fa_locked_until',
        'last_verification_otp_sent_at',
        'last_password_reset_sent_at',
        'last_2fa_otp_sent_at',
        'last_email_change_otp_sent_at',
    )
    actions = (
        'activate_users',
        'deactivate_users',
        'unlock_accounts',
        'disable_2fa',
        'logout_selected_users',
        'clear_pending_security_codes',
    )

    fieldsets = (
        (_('Credentials'), {
            'fields': ('email', 'password'),
        }),
        (_('Personal Details'), {
            'fields': ('name', 'image', 'image_preview'),
        }),
        (_('Permissions'), {
            'classes': ('collapse',),
            'fields': (
                'is_active',
                'is_staff',
                'is_superuser',
                'groups',
                'user_permissions',
            ),
        }),
        (_('Account Security'), {
            'classes': ('collapse',),
            'fields': (
                'failed_login_attempts',
                'locked_until',
                'last_login_ip',
            ),
        }),
        (_('Email Verification OTP'), {
            'classes': ('collapse',),
            'fields': (
                'otp',
                'otp_created_at',
                'otp_expires_at',
                'otp_attempts',
                'otp_locked_until',
            ),
        }),
        (_('Password Reset OTP'), {
            'classes': ('collapse',),
            'fields': (
                'password_reset_otp',
                'password_reset_otp_created_at',
                'password_reset_otp_expires_at',
                'password_reset_otp_attempts',
                'password_reset_otp_locked_until',
            ),
        }),
        (_('Email Change'), {
            'classes': ('collapse',),
            'fields': (
                'pending_email',
                'pending_email_otp',
                'pending_email_otp_created_at',
                'pending_email_otp_expires_at',
                'pending_email_otp_attempts',
                'pending_email_otp_locked_until',
            ),
        }),
        (_('Two-Factor Authentication'), {
            'classes': ('collapse',),
            'fields': (
                'is_2fa_enabled',
                'two_fa_method',
                'two_fa_otp',
                'two_fa_otp_created_at',
                'two_fa_otp_expires_at',
                'two_fa_attempts',
                'two_fa_locked_until',
            ),
        }),
        (_('Cooldown Timestamps'), {
            'classes': ('collapse',),
            'fields': (
                'last_verification_otp_sent_at',
                'last_password_reset_sent_at',
                'last_2fa_otp_sent_at',
                'last_email_change_otp_sent_at',
            ),
        }),
        (_('Important Dates'), {
            'classes': ('collapse',),
            'fields': ('last_login', 'created_at', 'updated_at'),
        }),
    )

    add_fieldsets = (
        (
            None,
            {
                'classes': ('wide',),
                'fields': ('name', 'email', 'password1', 'password2'),
            },
        ),
    )

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="width:40px;height:40px;object-fit:cover;border-radius:50%;" />',
                obj.image.url
            )
        return "No Image"

    image_preview.short_description = "Profile"

    def account_lock_status(self, obj):
        if obj.locked_until:
            return format_html(
                '<span style="color:#b91c1c;font-weight:600;">{}</span>',
                'Locked'
            )
        return format_html(
            '<span style="color:#15803d;font-weight:600;">{}</span>',
            'Open'
        )

    account_lock_status.short_description = "Lock Status"

    @admin.action(description='Activate selected users')
    def activate_users(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} user(s) activated.', messages.SUCCESS)

    @admin.action(description='Deactivate selected users')
    def deactivate_users(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} user(s) deactivated.', messages.SUCCESS)

    @admin.action(description='Unlock selected accounts')
    def unlock_accounts(self, request, queryset):
        updated = queryset.update(
            failed_login_attempts=0,
            locked_until=None,
            otp_attempts=0,
            otp_locked_until=None,
            password_reset_otp_attempts=0,
            password_reset_otp_locked_until=None,
            pending_email_otp_attempts=0,
            pending_email_otp_locked_until=None,
            two_fa_attempts=0,
            two_fa_locked_until=None,
        )
        self.message_user(request, f'{updated} account(s) unlocked.', messages.SUCCESS)

    @admin.action(description='Disable 2FA for selected users')
    def disable_2fa(self, request, queryset):
        updated = queryset.update(
            is_2fa_enabled=False,
            two_fa_method=None,
            two_fa_otp=None,
            two_fa_otp_created_at=None,
            two_fa_otp_expires_at=None,
            two_fa_attempts=0,
            two_fa_locked_until=None,
        )
        self.message_user(request, f'2FA disabled for {updated} user(s).', messages.SUCCESS)

    @admin.action(description='Logout selected users from all devices')
    def logout_selected_users(self, request, queryset):
        for user in queryset:
            logout_all_user_sessions(user)
        self.message_user(request, f'{queryset.count()} user(s) logged out from all devices.', messages.SUCCESS)

    @admin.action(description='Clear pending security codes')
    def clear_pending_security_codes(self, request, queryset):
        updated = queryset.update(
            otp=None,
            otp_created_at=None,
            otp_expires_at=None,
            otp_attempts=0,
            otp_locked_until=None,
            password_reset_otp=None,
            password_reset_otp_created_at=None,
            password_reset_otp_expires_at=None,
            password_reset_otp_attempts=0,
            password_reset_otp_locked_until=None,
            pending_email=None,
            pending_email_otp=None,
            pending_email_otp_created_at=None,
            pending_email_otp_expires_at=None,
            pending_email_otp_attempts=0,
            pending_email_otp_locked_until=None,
            two_fa_otp=None,
            two_fa_otp_created_at=None,
            two_fa_otp_expires_at=None,
            two_fa_attempts=0,
            two_fa_locked_until=None,
        )
        self.message_user(request, f'Security codes cleared for {updated} user(s).', messages.SUCCESS)


@admin.register(LoginHistory)
class LoginHistoryModelAdmin(admin.ModelAdmin):
    model = LoginHistory

    list_display = (
        'user',
        'ip_address',
        'short_user_agent',
        'login_time',
        'is_successful',
        'failure_reason',
    )
    list_filter = ('is_successful', 'login_time')
    search_fields = ('user__email', 'ip_address', 'user_agent', 'failure_reason')
    date_hierarchy = 'login_time'
    ordering = ('-login_time',)
    readonly_fields = (
        'user',
        'ip_address',
        'user_agent',
        'login_time',
        'is_successful',
        'failure_reason',
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def short_user_agent(self, obj):
        if not obj.user_agent:
            return '-'
        return obj.user_agent[:80]

    short_user_agent.short_description = 'User Agent'


@admin.register(UserSession)
class UserSessionModelAdmin(admin.ModelAdmin):
    model = UserSession

    list_display = (
        'id',
        'user',
        'ip_address',
        'browser',
        'operating_system',
        'device_type',
        'location_country',
        'location_city',
        'short_user_agent',
        'created_at',
        'last_activity',
        'is_active',
    )
    list_filter = ('is_active', 'created_at', 'last_activity')
    search_fields = (
        'user__email',
        'ip_address',
        'user_agent',
        'session_jti',
        'device_fingerprint',
        'browser',
        'operating_system',
        'device_type',
        'location_city',
        'location_region',
        'location_country',
        'location_timezone',
    )
    date_hierarchy = 'last_activity'
    ordering = ('-last_activity',)
    readonly_fields = (
        'user',
        'refresh_token',
        'ip_address',
        'user_agent',
        'session_jti',
        'device_fingerprint',
        'browser',
        'operating_system',
        'device_type',
        'location_city',
        'location_region',
        'location_country',
        'location_timezone',
        'location_latitude',
        'location_longitude',
        'created_at',
        'last_activity',
    )
    actions = ('deactivate_sessions',)

    @admin.action(description='Mark selected sessions inactive')
    def deactivate_sessions(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} session(s) marked inactive.', messages.SUCCESS)

    def short_user_agent(self, obj):
        if not obj.user_agent:
            return '-'
        return obj.user_agent[:80]

    short_user_agent.short_description = 'User Agent'


@admin.register(TwoFALog)
class TwoFALogModelAdmin(admin.ModelAdmin):
    model = TwoFALog

    list_display = (
        'user',
        'action',
        'ip_address',
        'short_user_agent',
        'status',
        'timestamp',
    )
    list_filter = ('action', 'status', 'timestamp')
    search_fields = ('user__email', 'ip_address', 'user_agent', 'status', 'action')
    date_hierarchy = 'timestamp'
    ordering = ('-timestamp',)
    readonly_fields = (
        'user',
        'action',
        'ip_address',
        'user_agent',
        'status',
        'timestamp',
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def short_user_agent(self, obj):
        if not obj.user_agent:
            return '-'
        return obj.user_agent[:80]

    short_user_agent.short_description = 'User Agent'
