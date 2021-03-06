
todo 
note that django's auth backend automatically returns True for any invocation of has_perm on a user which has is_superuser
But, the site is designed so that permissions depend on the user's active_role... 
so it looks weird to users with the is_superuser property... not sure how to fix this

one way to do this would be to add another role, SITE_ADMIN
another way would be to override is_admin on the user model
distinguish roles ADMIN and SITE_ADMIN


identity management
-------------------

1. represent relationships between parent, child, teacher, and classroom
2. integrate users into above representation
3. manage permissions based on above integration


functionality overview
----------------------

worktime
- index: list family's worktime commitments
- calendar: tabulate in calendar all worktime commitments
- move: edit worktime commitments
- prefer: handle initial slot requests
- map slot assignments to commitments

people/identification
- standard+social registration
- code to affiliate with classroom
- affiliate users with families of children
 
people
------

identification flow

1. administrator inserts initial data:
- identifiers of all children
- worktime duty amounts per child
- email addresses of responsible persons ("parents") per child

2. site circulates email to all parent addresses
- email includes authentication-affiliation token
- token identifies user and names classroom affiliation
- user then conventionally registers: either username-password, or social authentication, or both

data structure

- many-one relationship of child to classroom
- one-many relationship of child to parents

4. identity management interface
<!-- - to construct child identities, use a form with a dozen textfields for child names -->
<!-- - to add parents, use form with one child per row, and two email fields per child -->


Apps
----------

worktime

people



Implementing parent identification flow
---------------------------------------

- invite
  - submit AddChildForm, with emails
  - create Invitation objects with email attribute
  - send invite emails, with URL-embedded token containing the email address
- accept: InviteAcceptView
  - accept GET request to URL (with embedded token)
  - extract token from URL, and verify
  - create user with extracted email address
  - redirect to signup page
- signup: SignupView
  - add authentication method: password or social account
    - if social account, populate user data with first and last names
  - add personal info


Todo for People app
-------------------

- permissions: who can create/manage classroom roster?
    - admin creates classroom, invites scheduler
    - scheduler manages roster of that classroom
    - parents of children in classroom can
        - view that classroom roster and schedule
        - edit their own worktime slots
- improve user's profile management
    - edit profile data
    - edit child data
    - user-editing profile info; add social accounts
    
- invite teachers (existing users or no)
