from django.db import models
from django.contrib.auth.models import BaseUserManager,AbstractBaseUser,PermissionsMixin

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

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']

    objects = UserManager()

    def __str__(self):
        return self.email
    
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

