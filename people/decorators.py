from django.contrib.auth import REDIRECT_FIELD_NAME
from django.shortcuts import render

def validate_invite_token(function=None,
                       login_url=None,
                       redirect_field_name=REDIRECT_FIELD_NAME):
    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            token = self.kwargs.get('token')
            try:
                models.ParentInvite.objects.get(token=token)
                return view_func(request, *args, **kwargs)
            except models.ParentInvite.DoesNotExist:
                return render(request,
                              'people/valid_invite_required.html')
            return _wrapped_view
    if function:
        return decorator(function)
    return decorator
        
