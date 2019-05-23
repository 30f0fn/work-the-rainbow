from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver

from people.models import User, Child, Classroom, RelateEmailToObject, Role

# parent_role, scheduler_role, teacher_role, admin_role, 

# todo clean up access to roles

@receiver(post_save, sender=User)
def relate_user_to_object(sender, instance, created, **kwargs):
    # print(f"relate_email_to_object: this function was called with instance={instance}, created={created}")
    if created:
        email = instance.email
        for leto in RelateEmailToObject.objects.filter(email=email):
            # print(f"related {email} to {leto.related_object}")
            leto.execute()



# def updater(group, related_class):
#     def handler(sender, pk_set, **kwargs):
#         for pk in pk_set:
#             user = User.objects.get(pk=pk)
#             getattr(group, 'update_membership')(user)
#             print(f'updating {group} membership')
#     relation_name = f'{group.name}_set'
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


# @receiver(m2m_changed, sender=Classroom.teacher_set.through)
# def update_teachers(sender, action, pk_set, **kwargs):
#     # print('updating teachers')
#     teacher_role = Role.objects.get(name='teacher')
#     for pk in pk_set:
#         user = User.objects.get(pk=pk)
#         teacher_role.update_membership(user)
                
    
# @receiver(m2m_changed, sender=Child.parent_set.through)
# def update_parents(sender, action, pk_set, **kwargs):
#     # print('updating parents')
#     parent_role = Role.objects.get(name='parent')
#     for pk in pk_set:
#         user = User.objects.get(pk=pk)
#         parent_role.update_membership(user)

