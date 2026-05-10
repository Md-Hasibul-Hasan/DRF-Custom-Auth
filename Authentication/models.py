from django.db import models
from django.contrib.auth.models import BaseUserManager,AbstractBaseUser,PermissionsMixin
from django.utils import timezone
from datetime import timedelta
from django.conf import settings

# Create your models here.

class UserManager(BaseUserManager):
    def create_user(self,name,email,password=None, password2=None):
        #creates and saves a User with the given email and password

        if not email:
            raise ValueError("Users must have an email address")
        
        user = self.model(
            name=name,
            email=self.normalize_email(email)
        )
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self,name,email,password=None,**extra_fields):
        extra_fields.setdefault('is_staff',True)
        extra_fields.setdefault('is_superuser',True)
        if extra_fields.get('is_staff') is not True:
            raise ValueError("Superuser must have is_staff=True")
        if extra_fields.get('is_superuser') is not True:
            raise ValueError("Superuser must have is_superuser=True")
        
        # creates and saves a superuser with the given email and password
        user = self.create_user(
            name=name, 
            email=email, 
            password=password
        )

        user.is_active = True 
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user

class User(AbstractBaseUser,PermissionsMixin):
    email = models.EmailField(max_length=255,unique=True)
    name = models.CharField(max_length=255)
    image = models.ImageField(upload_to='profile_images/',null=True,blank=True)
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    
    # Account security fields
    failed_login_attempts = models.IntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    otp_attempts = models.IntegerField(default=0)
    otp_locked_until = models.DateTimeField(null=True, blank=True)
    last_otp_sent_at = models.DateTimeField(null=True, blank=True)
    
    # OTP verification fields
    otp = models.CharField(max_length=6, null=True, blank=True)
    otp_created_at = models.DateTimeField(null=True, blank=True)
    otp_expires_at = models.DateTimeField(null=True, blank=True)

    # Pending email change fields
    pending_email = models.EmailField(max_length=255, null=True, blank=True)
    pending_email_otp = models.CharField(max_length=6, null=True, blank=True)
    pending_email_otp_created_at = models.DateTimeField(null=True, blank=True)
    pending_email_otp_expires_at = models.DateTimeField(null=True, blank=True)
    
    # 2FA fields
    is_2fa_enabled = models.BooleanField(default=False)
    two_fa_method = models.CharField(max_length=20, choices=[('email', 'Email OTP')], default='email', null=True, blank=True)
    two_fa_otp = models.CharField(max_length=6, null=True, blank=True)
    two_fa_otp_created_at = models.DateTimeField(null=True, blank=True)
    two_fa_otp_expires_at = models.DateTimeField(null=True, blank=True)
    two_fa_attempts = models.IntegerField(default=0)
    two_fa_locked_until = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']

    objects = UserManager()

    def is_account_locked(self):
        """Check if account is locked and unlock if lock period expired"""
        if self.locked_until:
            if timezone.now() > self.locked_until:
                self.locked_until = None
                self.failed_login_attempts = 0
                self.save()
                return False
            return True
        return False

    def generate_otp(self):
        """Generate a 6-digit OTP and set expiration time"""
        import random
        self.otp = str(random.randint(100000, 999999))
        self.otp_created_at = timezone.now()
        self.otp_expires_at = timezone.now() + timedelta(seconds=settings.OTP_EXPIRE_TIMEOUT)  # OTP valid for 10 minutes

        self.otp_attempts = 0
        self.otp_locked_until = None
        self.last_otp_sent_at = timezone.now()

        self.save()
        return self.otp

    def verify_otp(self, otp):

        # check lock
        if self.otp_locked_until:
            if timezone.now() < self.otp_locked_until:
                return False
            else:
                self.otp_locked_until = None
                self.otp_attempts = 0
                self.save()

        # check otp exists
        if not self.otp or not self.otp_expires_at:
            return False

        # check expiry
        if timezone.now() > self.otp_expires_at:
            return False

        # wrong otp
        if self.otp != otp:
            self.otp_attempts += 1

            # lock after 5 failed attempts
            if self.otp_attempts >= settings.MAX_WRONG_OTP_ATTEMPTS:
                self.otp_locked_until = timezone.now() + timedelta(seconds=settings.OTP_LOCKED_TIMEOUT)

            self.save()
            return False

        # success → clear otp
        self.otp = None
        self.otp_created_at = None
        self.otp_expires_at = None
        self.otp_attempts = 0
        self.otp_locked_until = None

        self.save()

        return True

    def generate_pending_email_otp(self, pending_email):
        """Generate an OTP for pending email change"""
        import random
        self.pending_email = pending_email.lower()
        self.pending_email_otp = str(random.randint(100000, 999999))
        self.pending_email_otp_created_at = timezone.now()
        self.pending_email_otp_expires_at = timezone.now() + timedelta(seconds=settings.OTP_EXPIRE_TIMEOUT)
        self.save()
        return self.pending_email_otp

    def verify_pending_email_otp(self, otp):
        """Verify the provided pending email OTP"""
        if not self.pending_email or not self.pending_email_otp or not self.pending_email_otp_expires_at:
            return False

        if timezone.now() > self.pending_email_otp_expires_at:
            return False

        if self.pending_email_otp != otp:
            return False

        self.pending_email_otp = None
        self.pending_email_otp_created_at = None
        self.pending_email_otp_expires_at = None
        self.save()
        return True

    def generate_2fa_otp(self):
        """Generate a 6-digit 2FA OTP and set expiration time"""
        import random
        self.two_fa_otp = str(random.randint(100000, 999999))
        self.two_fa_otp_created_at = timezone.now()
        self.two_fa_otp_expires_at = timezone.now() + timedelta(seconds=settings.OTP_EXPIRE_TIMEOUT)  # 2FA OTP valid for 10 minutes
        self.two_fa_attempts = 0
        self.two_fa_locked_until = None
        self.save()
        return self.two_fa_otp

    def verify_2fa_otp(self, otp):
        """Verify the provided 2FA OTP with rate limiting"""
        # Check if account is locked
        if self.two_fa_locked_until:
            if timezone.now() < self.two_fa_locked_until:
                return False
            else:
                self.two_fa_locked_until = None
                self.two_fa_attempts = 0
                self.save()
        
        # Check if OTP exists and hasn't expired
        if not self.two_fa_otp or not self.two_fa_otp_expires_at:
            return False
        
        if timezone.now() > self.two_fa_otp_expires_at:
            return False
        
        # Verify OTP
        if self.two_fa_otp != otp:
            self.two_fa_attempts += 1
            if self.two_fa_attempts >= settings.MAX_WRONG_OTP_ATTEMPTS:
                self.two_fa_locked_until = timezone.now() + timedelta(seconds=settings.OTP_LOCKED_TIMEOUT)
            self.save()
            return False
        
        # Clear 2FA OTP after successful verification
        self.two_fa_otp = None
        self.two_fa_otp_created_at = None
        self.two_fa_otp_expires_at = None
        self.two_fa_attempts = 0
        self.two_fa_locked_until = None
        self.save()
        return True

    def is_2fa_locked(self):
        """Check if 2FA is locked due to too many failed attempts"""
        if self.two_fa_locked_until:
            if timezone.now() > self.two_fa_locked_until:
                self.two_fa_locked_until = None
                self.two_fa_attempts = 0
                self.save()
                return False
            return True
        return False

    def __str__(self):
        return self.email


class LoginHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='login_history')
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    login_time = models.DateTimeField(auto_now_add=True)
    is_successful = models.BooleanField(default=True)
    failure_reason = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        ordering = ['-login_time']

    def __str__(self):
        return f"{self.user.email} - {self.login_time}"
    
    def has_perm(self,perm,obj=None):
        "Does the user have a specific permission?"
        if self.is_superuser:
            return True
        return super().has_perm(perm,obj)
    
    def has_module_perms(self,app_label):
        "Does the user have permissions to view the app `app_label`?"
        if self.is_superuser:
            return True
        return super().has_module_perms(app_label)


class UserSession(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sessions'
    )

    refresh_token = models.TextField()

    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True
    )

    user_agent = models.TextField(
        null=True,
        blank=True
    )

    session_jti = models.CharField(
    max_length=255,
    null=True,
    blank=True
)

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    last_activity = models.DateTimeField(
        auto_now=True
    )

    is_active = models.BooleanField(
        default=True
    )

    def __str__(self):
        return f"{self.user.email} - Session"



class TwoFALog(models.Model):
    """Track 2FA events for audit logging"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='two_fa_logs')
    action = models.CharField(
        max_length=50,
        choices=[
            ('setup', 'Setup 2FA'),
            ('enable', 'Enable 2FA'),
            ('verify', 'Verify 2FA'),
            ('disable', 'Disable 2FA'),
            ('failed_attempt', 'Failed 2FA Attempt'),
        ]
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=[('success', 'Success'), ('failed', 'Failed')], default='success')
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.user.email} - {self.action} - {self.timestamp}"

