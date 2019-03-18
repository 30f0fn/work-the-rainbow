from django import template
from django.utils.html import format_html, format_html_join
from django.urls import reverse

register = template.Library()

@register.filter
def modelname(model):
    return model.__name__


@register.simple_tag
def display_u(user):
    # display = f'<a href=\'mailto:{user.email}\'>{user.username}</a>'
    # return format_html("<a href=\"mailto:{}\">{}</a>",
                       # user.email, user.username)
    return format_html("<a href=\"{}\">{}</a>",
                       reverse('public-profile',
                               kwargs={'username' : user.username}),
                       user.first_name)

@register.simple_tag
def display_child(child):
    nickname = child.nickname
    return format_html("<a href=\"{}\">{}</a>",
                       reverse('child-detail',
                               kwargs={'nickname' : nickname }),
                       child.nickname)



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
