from django.db.models.signals import post_save, m2m_changed, pre_save
from django.dispatch import receiver

from people.models import User, Child, Classroom, RelateEmailToObject, Role
from people.roles import *
import people.notifications

@receiver(pre_save, sender=Child)
def child_to_new_classroom(sender, *args, **kwargs):
    """update"""
    child_instance = kwargs['instance']
    if getattr(child_instance, 'pk') is None:
        return
    new_classroom = child_instance.classroom
    old_classroom = Child.objects.get(pk=child_instance.pk).classroom
    if old_classroom != new_classroom:
        default_user = User.objects.first()
        people.notifications.announce_child_to_new_classroom(
            default_user,
            child_instance, old_classroom, new_classroom)


@receiver(post_save, sender=User)
def relate_user_to_object(sender, instance, created, **kwargs):
    # print(f"relate_email_to_object: this function was called with instance={instance}, created={created}")
    if created:
        email = instance.email
        for leto in RelateEmailToObject.objects.filter(email=email):
            # print(f"related {email} to {leto.related_object}")
            leto.execute()

@receiver(m2m_changed, sender=Classroom.teacher_set.through)
def update_teachers(sender, action, pk_set, **kwargs):
    for pk in pk_set:
        user = User.objects.get(pk=pk)
        TEACHER.update_membership(user)

@receiver(m2m_changed, sender=Classroom.scheduler_set.through)
def update_schedulers(sender, action, pk_set, **kwargs):
    # print("received scheduler_update signal")
    for pk in pk_set:
        user = User.objects.get(pk=pk)
        SCHEDULER.update_membership(user)

@receiver(m2m_changed, sender=Child.parent_set.through)
def update_parents(sender, action, pk_set, **kwargs):
    for pk in pk_set:
        user = User.objects.get(pk=pk)
        PARENT.update_membership(user)

# def updater(role, related_class):
#     def handler(sender, pk_set, **kwargs):
#         for pk in pk_set:
#             user = User.objects.get(pk=pk)
#             getattr(role, 'update_membership')(user)
#             print(f'updating {role} membership')
#     relation_name = f'{role.name}_set'
#     rcvr = receiver(m2m_changed,
#                     sender=getattr(related_class,relation_name).through)
#     return rcvr(handler)

# parent_role_updater = updater(parent)
# scheduler_role_updater = updater(scheduler)
# teacher_role_updater = updater(teacher_role, Classroom)
# admin_role_updater = updater(admins)


# parent_role = Role.objects.get(name='parent')
# teacher_role = Role.objects.get(name='teacher')
# scheduler_role = Role.objects.get(name='scheduler')
# admin_role = Role.objects.get(name='admin')


# @receiver(m2m_changed, sender=Classroom.scheduler_set.through)
# def update_schedulers(sender, action, pk_set, **kwargs):
#     # print('updating schedulers')
#     scheduler_role = Role.objects.get(name='scheduler')
#     for pk in pk_set:
#         user = User.objects.get(pk=pk)
#         scheduler_role.update_membership(user)


                
    
# @receiver(m2m_changed, sender=Child.parent_set.through)
# def update_parents(sender, action, pk_set, **kwargs):
#     # print('updating parents')
#     parent_role = Role.objects.get(name='parent')
#     for pk in pk_set:
#         user = User.objects.get(pk=pk)
#         parent_role.update_membership(user)

