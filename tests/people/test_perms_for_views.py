"""
people view perms:

view_classroom
edit_classroom
view_child_profile
edit_child
admin
create_classroom

people view mixins:

loginrequiredmixin
permissionrequiredmixin

childmixin < childeditmixin
classroommixin < classroomeditmixin

adminmixin
profiledatamixin

* note - some mixins impose permission requirements, others modify view functionality, some do both
- need explicit tests only for the permission component
- i.e. for view and edit of child and classroom
- view_child: is_admin, is_parent_in_classroom_of, is_teacher_of, is_scheduler
- edit_child: is_admin, is_parent_of, is_scheduler_for_child
- view_classroom: is_admin, is_parent_in_classroom, is_scheduler_in_classroom, is_teacher_in
- edit_classroom: is_scheduler_in, is_admin

So need the following "positive" permission test mixins:
absolute:
- is_admin, 
child-predicated: 
- is_parent_in_classroom_of, is_teacher_of, is_parent_of, is_scheduler_in_classroom_of 
classroom-predicated: 
- is_parent_in, is_scheduler_in, is_teacher_in

these require the following data:
- admin_user, child_in_classroom, teacher_in_classroom, parent_of_child, scheduler_in_classroom, parent_in_classroom


for "negative" test mixins, try users with maximal insufficient permissions


"""


#############################################
# resources for "positive" permission tests #
#############################################


class _PermittedWithLoginBase(object):
    def permitted_with_login(self, username, password):
        self.client.login(username=username,
                          password=password)
        response = self.client.get(
            self.vut_url())
        self.assertEqual(response.status_code, 200)


########################################
# atomic positive permission verifiers #
########################################

class _PermittedForUser(object):
    def test_permitted_for_user(self):
        return self.permitted_with_login('user', 'user_pw')


class _PermittedForAdmin(object):
    def test_permitted_for_admin(self):
        return self.permitted_with_login('admin', 'admin_pw')

class _PermittedForParentOf(object):
    def test_permitted_for_parent_of(self):
        return self.permitted_with_login('parent', 'parent_pw')

class _PermittedForParentInClassroomOf(object):
    def test_permitted_for_parent_in_classroom_of(self):
        return self.permitted_with_login('parent_2', 'parent_2_pw')
    
class _PermittedForSchedulerInClassroomOf(object):    
    def test_permitted_for_scheduler_in_classroom_of(self):
        return self.permitted_with_login('scheduler', 'scheduler_pw')

class _PermittedForTeacherInClassroomOf(object):    
    def test_permitted_for_teacher_in_classroom_of(self):
        return self.permitted_with_login('teacher', 'teacher_pw')

class _PermittedForParentIn(object):
    def test_permitted_for_parent_in(self):
        return self.permitted_with_login('parent_2', 'parent_2_pw')

class _PermittedForSchedulerIn(object):
    def test_permitted_for_scheduler_in(self):
        return self.permitted_with_login('scheduler', 'scheduler_pw')

class _PermittedForTeacherIn(object):
    def test_permitted_for_teacher_in(self):
        return self.permitted_with_login('teacher', 'teacher_pw')

##########################################
# compound positive permission verifiers #
##########################################

class _ClassroomMixinPositivePerm(_PermittedForParentIn,
                                          _PermittedForSchedulerIn,
                                          _PermittedForTeacherIn,
                                          _PermittedForAdmin,
                                          _PermittedWithLoginBase):
    pass

class _ClassroomEditMixinPositivePerm(_PermittedForSchedulerIn,
                                         _PermittedForAdmin,
                                         _PermittedWithLoginBase):
    pass

class _ChildMixinPositivePerm(_PermittedForParentInClassroomOf,
                                      _PermittedForSchedulerInClassroomOf,
                                      _PermittedForTeacherInClassroomOf,
                                      _PermittedForAdmin,
                                      _PermittedWithLoginBase):
    pass

class _ChildEditMixinPositivePerm(_PermittedForParentOf,
                            _PermittedForSchedulerInClassroomOf,
                            _PermittedForAdmin,
                            _PermittedWithLoginBase):
    pass


#############################################
# resources for "negative" permission tests #
#############################################



class _ForbiddenDespiteLoginBase(object):

    def forbidden_despite_login(self, username, password):
        self.client.login(username=username,
                          password=password)
        response = self.client.get(
            self.vut_url())
        self.assertEqual(response.status_code, 403)


############################################
# elementary negative permission verifiers #
############################################

class _LoginRequired(object):

    def test_redirect_if_not_logged_in(self):
        response = self.client.get(
            self.vut_url())
        self.assertRedirects(response,
                             f'/accounts/login/?next={self.vut_url()}')

#################################
# negative permission verifiers #
#################################

class _ForbiddenForNonAdminUsersNotInClassroom(object):
    def test_forbidden_for_mere_user(self):
        self.forbidden_despite_login('user', 'user_pw')
    def test_forbidden_for_parent_in_other_classroom(self):
        self.forbidden_despite_login('parent_3', 'parent_3_pw')
    def test_forbidden_for_scheduler_in_other_classroom(self):
        self.forbidden_despite_login('scheduler_2', 'scheduler_2_pw')
    def test_forbidden_for_teacher_in_other_classroom(self):
        self.forbidden_despite_login('teacher_2', 'teacher_2_pw')

class _ForbiddenForNonAdmin(object):
    def test_forbidden_for_mere_user(self):
        self.forbidden_despite_login('user', 'user_pw')
    def test_forbidden_for_parent(self):
        self.forbidden_despite_login('parent', 'parent_pw')
    def test_forbidden_for_scheduler(self):
        self.forbidden_despite_login('scheduler', 'scheduler_pw')
    def test_forbidden_for_teacher(self):
        self.forbidden_despite_login('teacher', 'teacher_pw')
    

class _ChildMixinNegativePerm(_ForbiddenForNonAdminUsersNotInClassroom,
                                      _LoginRequired,
                                      _ForbiddenDespiteLoginBase):
    pass

class _ClassroomMixinNegativePerm(_ForbiddenForNonAdminUsersNotInClassroom,
                                          _LoginRequired,
                                          _ForbiddenDespiteLoginBase):
    pass

class _ChildEditMixinNegativePerm(_ForbiddenForNonAdminUsersNotInClassroom,
                                          _LoginRequired,
                                          _ForbiddenDespiteLoginBase):
    def test_forbidden_for_parent_of_other_child(self):
        self.forbidden_despite_login('parent_2', 'parent_2_pw')
    def test_forbidden_for_teacher(self):
        self.forbidden_despite_login('teacher', 'teacher_pw')    

class _ClassroomEditMixinNegativePerm(_ForbiddenForNonAdminUsersNotInClassroom,
                                              _LoginRequired,
                                              _ForbiddenDespiteLoginBase):
    def test_forbidden_for_parent(self):
        self.forbidden_despite_login('parent', 'parent_pw')
    def test_forbidden_for_teacher(self):
        self.forbidden_despite_login('teacher', 'teacher_pw')    

    
#################################################
# combined permission verifiers for view mixins #
#################################################

class ClassroomEditMixinPermTestMixin(_ClassroomEditMixinNegativePerm,
                                      _ClassroomEditMixinPositivePerm):
    pass

class ClassroomMixinPermTestMixin(_ClassroomMixinNegativePerm,
                                  _ClassroomMixinPositivePerm):
    pass

class ChildEditMixinPermTestMixin(_ChildEditMixinNegativePerm,
                                  _ChildEditMixinPositivePerm):
    pass

class ChildMixinPermTestMixin(_ChildMixinNegativePerm,
                              _ChildMixinPositivePerm):
    pass

class AdminMixinPermTestMixin(_ForbiddenForNonAdmin,
                              _PermittedForAdmin,
                              _PermittedWithLoginBase,
                              _ForbiddenDespiteLoginBase):
    pass

class PermittedForUserTestMixin(_PermittedForUser,
                                _LoginRequired,
                                _PermittedWithLoginBase,
                                _ForbiddenDespiteLoginBase):
    pass



























