"""
Ophiron Profile Models
Model for user profile image
"""

from django.db import models
from django.contrib.auth.models import User
from django.core.files.storage import default_storage
import os

def user_profile_upload_path(instance, filename):
    """Upload path for user profile image"""
    return f'profiles/{instance.user.username}/{filename}'

class UserProfile(models.Model):
    """User profile model"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    profile_image = models.ImageField(
        upload_to=user_profile_upload_path,
        null=True,
        blank=True,
        help_text="Profile image (JPG, PNG, GIF, WebP - Max 5MB)"
    )
    
    # Personal Information
    full_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Full name of the user"
    )
    email = models.EmailField(
        blank=True,
        null=True,
        help_text="Personal email address"
    )
    
    # System Preferences
    timezone = models.CharField(
        max_length=100,
        default='UTC',
        help_text="User's preferred timezone"
    )
    language = models.CharField(
        max_length=10,
        default='en',
        help_text="User's preferred language"
    )
    
    # Profile completion tracking
    is_profile_complete = models.BooleanField(
        default=False,
        help_text="Whether user has completed their profile setup"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"
    
    def __str__(self):
        return f"{self.user.username} Profile"
    
    @property
    def has_profile_image(self):
        """Check if profile image exists"""
        return bool(self.profile_image and self.profile_image.name)
    
    @property
    def profile_image_url(self):
        """Return profile image URL"""
        if self.has_profile_image:
            return self.profile_image.url
        return '/static/images/demo-avatar.svg'
    
    def delete_profile_image(self):
        """Delete profile image"""
        if self.profile_image and self.profile_image.name:
            if default_storage.exists(self.profile_image.name):
                default_storage.delete(self.profile_image.name)
            self.profile_image = None
            self.save()
    
    def check_profile_completion(self):
        """Check if profile is complete"""
        required_fields = ['full_name', 'email', 'timezone']
        return all(getattr(self, field) for field in required_fields)
    
    def mark_profile_complete(self):
        """Mark profile as complete if all required fields are filled"""
        if self.check_profile_completion():
            self.is_profile_complete = True
            # Don't call save() here to avoid infinite recursion
    
    def save(self, *args, **kwargs):
        # Delete old image
        if self.pk:
            old_instance = UserProfile.objects.get(pk=self.pk)
            if old_instance.profile_image and old_instance.profile_image != self.profile_image:
                if default_storage.exists(old_instance.profile_image.name):
                    default_storage.delete(old_instance.profile_image.name)
        
        super().save(*args, **kwargs)
        
        # Check profile completion after save
        self.mark_profile_complete()
