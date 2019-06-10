# from enum import Enum

from people.models import Role

# class roles(Enum):
    # TEACHER = Role.objects.get(name='teacher')
    # SCHEDULER = Role.objects.get(name='scheduler')
    # PARENT = Role.objects.get(name='parent')
    # ADMIN = Role.objects.get(name='admin')

    
TEACHER, _ = Role.objects.get_or_create(name='teacher')
SCHEDULER, _ = Role.objects.get_or_create(name='scheduler')
PARENT, _ = Role.objects.get_or_create(name='parent')
ADMIN, _ = Role.objects.get_or_create(name='admin')
NULL_ROLE, _ = Role.objects.get_or_create(name='null')
