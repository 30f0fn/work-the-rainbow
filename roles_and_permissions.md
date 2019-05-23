Role API

roles are: Parent, Teacher, Scheduler, Admin
these are instances of Role class
each has a membership predicate "accepts"
the roles of a user are the roles which accept that user 

ensure that user.active_role always belongs to user.roles

for given role,
- check whether user has it
- add/remove role from user

for given user, enumerate the roles it has
  * for each role, check whether user has it and yield it if true


role.accepts
------

- user.roles

user.active_role
-----------

- base.html, as condition for including base_nav.html
- base_nav.html for role_navigator
- redirect user to the main view of their active_role (from base url for authenticated user)
- when loading main view of role, set active_role to that role (invoked upon explicit request of e.g. ParentHomeView, from {% url 'parent-home' %} in base_nav)

user.roles
----------

- base.html
- base_nav.html
- has_multi_roles

user.multi_roles
--------------------

- in base_nav.html, for determining whether to show role navigator







for given user, get/set its active role

Uses of roles:

- role navigation bar (has_multi_roles; active vs inactive)
- role-subordinate views: home, etc.
