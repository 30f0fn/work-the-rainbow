from django.db.models.signals import post_save
from django.dispatch import receiver
from people.models import User, RelateEmailToObject



@receiver(post_save, sender=User)
def relate_user_to_object(sender, instance, created, **kwargs):
    print(f"relate_email_to_object: this function was called with instance={instance}, created={created}")
    if created:
        email = instance.email
        for leto in RelateEmailToObject.objects.filter(email=email):
            print(f"related {email} to {leto.related_object}")
            leto.execute()
