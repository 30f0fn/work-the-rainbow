import rules
from people.models import Classroom
from people.rules import is_admin, is_teacher, is_parent, is_scheduler, is_scheduler_in_classroom, is_teacher_in_classroom, is_teacher_of

@rules.predicate
def owns_worktimecommitment(user, worktimecommitment):
    return user.active_role == PARENT and\
        user in worktimecommitment.child.parents

rules.add_rule('main.edit_worktimecommitment',
               is_admin | 
               is_scheduler_in_classroom |
               owns_worktimecommitment)

rules.add_perm('main.score_worktime_attendance',
               is_admin | 
               is_teacher_in_classroom)
