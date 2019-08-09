import rules
from people.models import Classroom
from people.roles import *

def acts_as(user, role):
    return user.is_authenticated and user.active_role() == role

@rules.predicate
def is_teacher(user):
    return acts_as(user, TEACHER)

@rules.predicate
def is_scheduler(user):
    return acts_as(user, SCHEDULER)

@rules.predicate
def is_parent(user):
    return acts_as(user, PARENT)

@rules.predicate
def is_admin(user):
    return acts_as(user, ADMIN)
    # return user.is_superuser

@rules.predicate
def is_parent_of(user, child):
    return acts_as(user, PARENT) and\
        user in child.parent_set.all()

@rules.predicate
def is_parent_in(user, classroom):
    return acts_as(user, PARENT) and\
        user in classroom.parents()
    # return user in classroom.parents()

@rules.predicate
def is_teacher_in(user, classroom):
    return acts_as(user, TEACHER) and\
        user in classroom.teacher_set.all()
    # return user in classroom.teacher_set.all()

@rules.predicate
def is_scheduler_in(user, classroom):
    return acts_as(user, SCHEDULER) and\
        user in classroom.scheduler_set.all()
    # return user in classroom.scheduler_set.all()

@rules.predicate
def is_scheduler_in_classroom_of(user, child):
    return acts_as(user, SCHEDULER) and\
        user in child.classroom.scheduler_set.all()
    # return user in child.classroom.scheduler_set.all()

@rules.predicate
def is_parent_in_classroom_of(user, child):
    return acts_as(user, PARENT) and\
        user in child.classroom.parents()
    # return user in child.classroom.parents()

@rules.predicate
def is_teacher_in_classroom_of(user, child):
    return acts_as(user, TEACHER) and\
        user in child.classroom.teacher_set.all()

rules.add_perm('people.edit_child',
               is_parent_of
               | is_scheduler_in_classroom_of
               | is_admin)

rules.add_perm('people.view_child_profile',
               is_admin |
               is_teacher_in_classroom_of |
               is_scheduler_in_classroom_of |
               is_parent_in_classroom_of)

rules.add_perm('people.create_classroom',
               is_admin)

rules.add_perm('people.edit_classroom',
               is_scheduler_in |
               is_admin)

rules.add_perm('people.view_classroom',
               is_teacher_in |
               is_parent_in |
               is_scheduler_in |
               is_admin)

rules.add_perm('admin',
               is_admin)



# admin
# is_scheduler user classroom
# is_parent user child
# parent_in_classroom
# teacher_in_classroom

