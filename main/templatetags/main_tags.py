from django import template
from django.utils.html import format_html, format_html_join

from django.urls import reverse

from notifications.templatetags import notifications_tags

register = template.Library()


@register.filter
def render_field_from_string(form, s):
    if s in form.fields:
        return form[s].as_widget()
    return ""

@register.filter
def render_field_from_int(form, n):
    if str(n) in form.fields:
        return form[str(n)].as_widget()
    return ""

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

@register.filter
def model_name(model):
    return getattr(model, '__name__',
                   model.__class__.__name__)
    # return model.__name__

@register.inclusion_tag('smart_link.html')
def smart_link(linked_url, link_text, request):
    return locals()

@register.simple_tag(takes_context=True)
def live_notifications_smartlink(context, badge_class='live_notifications_smartlink'):
    user = notifications_tags.user_context(context)
    if not user:
        return ''
    html = "<span class='{badge_class}'>notifications ({unread})</span>".format(
        badge_class=badge_class,
        unread=user.notifications.unread().count(),
    )
    if 'notifications' not in context['request'].path:
        html = "<a href='{link_url}'>{html}</a>".format(
            link_url=reverse('notifications'),
            html=html
        )
    html = "<li>{html}</li>".format(html=html)
    return format_html(html)

# @register.inclusion_tag('notifications_badge.html')
# def smart_link(linked_url, link_text, request):
#     link_text = f'notifications ({})'
#     return locals()



# @register.filter
# def modelname(model):
#     return model.__name__

# def display_user(user):
#     display = f'<a href=\'mailto:{user.email}\'>{user.username}</a>'
#     return format_html("<a href=\"mailto:{}\">{}</a>",
#                        user.email, user.username)

# @register.simple_tag
# def user(user):
#     return display_user(user)

# @register.filter
# def display_user_list(ul):
#     return format_html_join(
#         ', ',
#         '<a href=\'mailto:{}\'>{}</a>',
#         ((u.email, u.username) for u in ul)
#     )

