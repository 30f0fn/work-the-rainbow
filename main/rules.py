import rules
from people.models import Classroom
from people.rules import is_admin, is_scheduler_in_classroom

@rules.predicate
def owns_worktimecommitment(user, worktimecommitment):
    return user in worktimecommitment.child.parents


rules.add_rule('main.edit_worktimecommitment',
               is_admin | 
               is_scheduler_in_classroom |
               owns_worktimecommitment)
