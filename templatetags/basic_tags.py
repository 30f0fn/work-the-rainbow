from django import template
from django.utils.html import format_html, format_html_join

register = template.Library()


{% with url_name=request.resolver_match.url_name %}
<li class="dropdown {% if url_name == 'index' %}active{% endif %}"
   <a href="{% url 'index' %}" >Home </a>
</li>
<li>...</li>
{% endwith %}


@register.tag
def 

# @register.filter
# def render_field_from_string(form, s):
#     if s in form.fields:
#         return form[s].as_widget()
#     return ""

# @register.filter
# def render_field_from_int(form, n):
#     if str(n) in form.fields:
#         return form[str(n)].as_widget()
#     return ""

# @register.filter
# def get_item(dictionary, key):
#     return dictionary.get(key)


# # @register.filter
# # def modelname(model):
# #     return model.__name__

# # def display_user(user):
# #     display = f'<a href=\'mailto:{user.email}\'>{user.username}</a>'
# #     return format_html("<a href=\"mailto:{}\">{}</a>",
# #                        user.email, user.username)

# # @register.simple_tag
# # def user(user):
# #     return display_user(user)

# # @register.filter
# # def display_user_list(ul):
# #     return format_html_join(
# #         ', ',
# #         '<a href=\'mailto:{}\'>{}</a>',
# #         ((u.email, u.username) for u in ul)
# #     )

