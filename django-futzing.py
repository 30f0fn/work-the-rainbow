
# from django.forms import Form, BooleanField

# class FutzForm(Form):
#     boo = BooleanField()

# ff = FutzForm({'boo':0})

from django.test.client import RequestFactory

rfac = RequestFactory()
getreq = rfac.get('')

from django.views import View
from django.views.generic import FormView


class View1(View):
    def get(self, request, *args, **kwargs):
        return "<p>here is some html</p>"

class MixinA(object):
    def dispatch(self, request, *args, **kwargs):
        self.a = 1
        retval = super().dispatch(request, *args, **kwargs)
        return retval

class ViewB(MixinA, FormView):
    def get_initial(self, *args, **kwargs):
        return super().get_initial(*args, **kwargs).update({'a': self.a})

vb = ViewB()
vb.dispatch(getreq)
