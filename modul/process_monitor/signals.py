"""
Process Monitor Signals
Tek admin sınırlaması ve diğer signal handler'lar
"""

from django.db.models.signals import pre_save
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.dispatch import receiver


@receiver(pre_save, sender=User)
def enforce_single_superuser(sender, instance, **kwargs):
    """
    Tek superuser sınırlaması
    Sistem sadece 1 superuser'a izin verir
    """
    if instance.is_superuser:
        # Eğer yeni bir superuser oluşturuluyorsa
        if not instance.pk:  # Yeni kullanıcı
            existing_superusers = User.objects.filter(is_superuser=True).count()
            if existing_superusers >= 1:
                raise ValidationError(
                    "❌ Sadece 1 admin kullanıcısı olabilir! "
                    "Mevcut admin kullanıcısını kaldırmadan yeni admin oluşturamazsınız."
                )
        else:  # Mevcut kullanıcı güncelleniyor
            # Eğer başka bir kullanıcıyı admin yapmaya çalışıyorsa
            existing_superusers = User.objects.filter(is_superuser=True).exclude(pk=instance.pk)
            if existing_superusers.exists():
                raise ValidationError(
                    "❌ Sadece 1 admin kullanıcısı olabilir! "
                    f"Mevcut admin: {existing_superusers.first().username}"
                )

