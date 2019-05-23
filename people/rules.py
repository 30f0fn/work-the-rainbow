import rules
from people.models import Classroom
from people.roles import *

# what supplies the arguments to the predicates?

@rules.predicate
def is_teacher(user):
    return user.active_role == TEACHER

@rules.predicate
def is_scheduler(user):
    return user.active_role == SCHEDULER

@rules.predicate
def is_parent(user):
    return user.active_role == PARENT

@rules.predicate
def is_admin(user):
    return user.active_role == ADMIN
    # return user.is_superuser


@rules.predicate
def is_parent_of(user, child):
    return user.active_role == PARENT and\
        user in child.parent_set.all()

    # return user in child.parent_set.all()

@rules.predicate
def is_parent_in_classroom(user, classroom):
    return user.active_role == PARENT and\
        user in classroom.parents
    # return user in classroom.parents

@rules.predicate
def is_teacher_in_classroom(user, classroom):
    return user.active_role == TEACHER and\
        user in classroom.teacher_set.all()
    # return user in classroom.teacher_set.all()

@rules.predicate
def is_scheduler_in_classroom(user, classroom):
    return user.active_role == SCHEDULER and\
        user in classroom.scheduler_set.all()
    # return user in classroom.scheduler_set.all()

@rules.predicate
def is_scheduler_for_child(user, child):
    return user.active_role == SCHEDULER and\
        user in child.classroom.scheduler_set.all()
    # return user in child.classroom.scheduler_set.all()

@rules.predicate
def is_parent_in_classroom_of(user, child):
    return user.active_role == PARENT and\
        user in child.classroom.parents
    # return user in child.classroom.parents

@rules.predicate
def is_teacher_of(user, child):
    return user.active_role == TEACHER and\
        user in child.classroom.teacher_set.all()



rules.add_perm('people.edit_child',
               is_parent_of
               | is_scheduler_for_child
               | is_admin
)

rules.add_perm('people.view_child_profile',
               is_admin |
               is_teacher_of |
               is_parent_in_classroom_of)

rules.add_perm('people.view_child_personal',
               is_admin |
               is_teacher_of |
               is_parent_of)

rules.add_perm('people.create_classroom',
               is_admin)

rules.add_perm('people.edit_classroom',
               is_scheduler_in_classroom |
               is_admin)

rules.add_perm('people.view_classroom',
               is_teacher_in_classroom |
               is_parent_in_classroom |
               is_scheduler_in_classroom |
               is_admin)

rules.add_perm('admin',
               is_admin)




# admin
# is_scheduler user classroom
# is_parent user child
# parent_in_classroom
# teacher_in_classroom

