
# from django.forms import Form, BooleanField

class FutzForm(Form):
    boo = BooleanField()

ff = FutzForm({'boo':0})

from django.test.client import RequestFactory

rfac = RequestFactory()
getreq = rfac.get('')

from django.views import View
from django.views.generic import FormView


class View1(View):
    def get(self, request, *args, **kwargs):
        return "<p>here is some html</p>"

    # def setup(self, request, *args, **kwargs):
        # super().setup(self, request, *args, **kwargs)
        # self.a = 1
    # def dispatch(self, request, *args, **kwargs):
    #     retval = super().dispatch(request, *args, **kwargs)
    #     self.a = 1
    #     return retval


class ViewB(MixinA, View1):
    pass
    # def dispatch(self, request, *args, **kwargs):
        # self.a = 1
    # def get_initial(self, *args, **kwargs):
        # return super().get_initial(*args, **kwargs).update({'a': self.a})

# vb = ViewB()
# vb.dispatch(getreq)
# vb.a


class MixinA(object):
    # pass
    def dispatch(self, request, *args, **kwargs):
        self.a = 1
        return super().dispatch(request, *args, **kwargs)


class MixinB(object):
    def dispatch(self, request, *args, **kwargs):
        self.b = self.a + self.a
        return super().dispatch(request, *args, **kwargs)

class ViewC(MixinA, MixinB, FormView):
    template_name = "generic_form"
    form_class = FutzForm
    def get_initial(self, *args, **kwargs):
        return super().get_initial(*args, **kwargs).update({'a': self.a})

vc = ViewC.as_view()
vc(getreq)
