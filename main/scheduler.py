import random, itertools

def generate_assignments(num_kids,
                         assignables_from_kid_index):

    def can_extend(taken, asgn):
        return any([offset in taken[asgn.shift_pk]
                    for offset in asgn.normalized_offsets()])

    def extend(branch, taken, asgn):
        for offset in asgn.shift.normalized_offsets():
            taken[asgn.shift_pk].add(offset)
        branch.append(asgn)

    def pop_branch(taken):
        asgn = branch.pop()
        for offset in asgn.shift.normalized_offsets():
            taken[asgn.shift_pk].remove(offset)

    def by_index(branch, taken):
        kid_index = len(branch)
        for asgn in assignables_from_kid_index(kid_index):
            if can_extend(taken, asgn):
                extend(branch, taken, asgn)
                if index + 1 == num_kids:
                    yield branch
                else:
                    for ret in by_index(branch):
                        yield ret
                        pop_branch(taken)

    branch, taken = [], defaultdict(set)
    return by_index(branch, taken)

def by_increasing_rank(kids, shifts, first_rank, second_rank, randomized=True):
    num_kids = len(kids)
    kid_indices = list(range(num_kids))
    for num_alternates in range(num_kids):
        all_alternates = list(itertools.combinations(kid_indices, num_alternates))
        if randomized:
            random.shuffle(alternates)
        for alternates in all_alternates:
            def assignables_from_kid_index(kid_index):
                return first_rank[kid_index] if kid_index not in alternates\
                    else second_rank[kid_index]
            yield generate_assignments(num_kids,
                                       assignables_from_kid_index)




# to add n lower-ranked assignments, choose n kids and replace their assignables with lower-ranked ones
# sort/filter by: rank, week-over-week variance, assigned-shifts-per-family 

# simple model: assign each kid an integer in range(n)

# a_b_k_i = [list(range(4)) for _ in range(3)]

# asgn_iter = generate_assignments(a_b_k_i, 4)
# for b in itertools.islice(asgn_iter, 0, 4):
#     print(b)








# import random
# import constraint
# from constraint import *
# import itertools

# from main.models import Shift, ShiftAssignment, ShiftAssignmentCollection
# from people.models import Classroom, Child

# """
# SIMPLE VERSION: just try to map shifts to families
# """

# # moved this to manager method of shiftassignmentcollection

# def create_optimal_shift_assignments(period, no_worse_than=1):
#     ShiftAssignmentCollection.objects.filter(period=period).delete()
#     problem = Problem()
#     families = Child.objects.filter(classroom=period.classroom)
#     for f, child in enumerate(families): 
#         accepted_shifts = Shift.objects.filter(
#             shiftpreference__child=child,
#             shiftpreference__rank__lte=no_worse_than)
#         problem.addVariable(f, accepted_shifts)
#     for c1,c2,c3 in itertools.combinations(range(len(families)), 3):
#         problem.addConstraint(lambda s1, s2, s3: not(s1 == s2 == s3),
#                               [c1, c2, c3])
#     retval = []
#     for solution in problem.getSolutions():
#         collection = ShiftAssignmentCollection.objects.create(period=period)
#         for f in range(len(families)):
#             ShiftAssignment.objects.get_or_create(child=families[f],
#                                                   period=period,
#                                                   shift=solution[f],
#                                                   collection=collection)
#         retval.append(solution)
#     return retval


# # for each shift, generate its instances in the period
# # get the families to whom it's assigned
# # apportion instances to families
# def create_commitments(period):
#     for sh in Shift.objects.all():
#         families = [sha.child for sha in sh.shiftassignment_set.all()]
#         sh_occs = list(sh.occurrences_for_date_range(period.start, period.end))
#         print(sh_occs)
#         print(families)
#         for index, child in enumerate(families):
#             # alternate weeks to assign
#             for occ in sh_occs[index::2]:
#                 commitment = occ.create_commitment(child)
#                 print(commitment)

  



#     # def create_commitments(self):
#     #     shifts = Shift.objects.filter(classroom=self.period.classroom)
#     #     assignments = self.shiftassignment_set.all()
#     #     offset = 0
#     #     for sh in shifts:
#     #         offset = offset + 1
#     #         available_indices = [(offset + i) % 4 for i in range(4)]
#     #         # instead of cycling the indices, keep a count of how many times an index has been used, then always pick the least-used index first
#     #         families = [assignment.child for assignment in assignments
#     #                     if assignment.shift == sh]
#     #         sh_occs = list(sh.occurrences_for_date_range(self.period.start,
#     #                                                      self.period.end))
#     #         assert(sum([child.shifts_per_month for child in families]) <= 4)
#     #         families.sort(key = lambda c : -c.shifts_per_month)
#     #         # so either [0,1,2,3] or [1,2,3,4]
#     #         def assign_from_index(child, index):
#     #             for occ in sh_occs[index::4]:
#     #                 commitment = occ.create_commitment(child)
#     #         for child in families:
#     #             first_index = available_indices.pop()
#     #             assign_from_index(child, first_index)
#     #             # available_indices.remove(first_index)
#     #             if child.shifts_per_month == 2:
#     #                 second_index = (first_index + 2) % 4
#     #                 # must be available, since child has at most one predecessor (else sum of children's shifts per months exceeds four), and that predecessor has different parity 
#     #                 available_indices.remove(second_index)
#     #                 assign_from_index(child, second_index)

