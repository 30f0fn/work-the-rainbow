import rules
from people.models import Classroom

# what supplies the arguments to the predicates?

@rules.predicate
def is_parent_of(user, child):
    return user in child.parent_set.all()


@rules.predicate
def is_parent_in_classroom(user, classroom):
    return classroom in Classroom.objects.filter(child__parent_set=user)
    # return user in Classroom.objects.filter(child__parent=profile)


@rules.predicate
def is_teacher_in_classroom(user, classroom):
    return user in classroom.teacher_set.all()


@rules.predicate
def is_scheduler_in_classroom(user, classroom):
    return user in classroom.scheduler_set.all()

@rules.predicate
def is_scheduler_for_child(user, child):
    return user in child.classroom.scheduler_set.all()



@rules.predicate
def is_admin(user):
    return user.is_superuser


rules.add_perm('people.edit_child',
               is_parent_of
               | is_scheduler_for_child
               | is_admin
)


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



# admin
# is_scheduler user classroom
# is_parent user child
# parent_in_classroom
# teacher_in_classroom

