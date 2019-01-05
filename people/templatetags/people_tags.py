from django import template

register = template.Library()

@register.filter
def modelname(model):
    return model.__name__

