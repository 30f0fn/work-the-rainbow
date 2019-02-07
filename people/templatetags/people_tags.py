from django import template
from django.utils.html import format_html, format_html_join

register = template.Library()

@register.filter
def modelname(model):
    return model.__name__

def display_user(user):
    display = f'<a href=\'mailto:{user.email}\'>{user.username}</a>'
    return format_html("<a href=\"mailto:{}\">{}</a>",
                       user.email, user.username)

@register.simple_tag
def user(user):
    return display_user(user)

@register.filter
def display_user_list(ul):
    return format_html_join(
        ', ',
        '<a href=\'mailto:{}\'>{}</a>',
        ((u.email, u.username) for u in ul)
    )

@register.filter
def addstr(arg1, arg2):
    """concatenate arg1 & arg2"""
    return str(arg1) + str(arg2)
