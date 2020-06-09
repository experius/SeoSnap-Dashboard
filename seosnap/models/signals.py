from django.contrib.auth.models import User
from django.db.models.signals import pre_save
from django.dispatch import receiver


@receiver(pre_save, sender=User)
def set_user_staff(sender, instance, **kwargs):
    instance.is_staff = True
