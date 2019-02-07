def inst_vars_from_method(method, properties):
    def new_method(self, *args, **kwargs):
        for key, value in properties.items():
            setattr(self, key, value)
        getattr(self.__class__.mro()[1], method)(self, *args, **kwargs)
    return new_method

def inst_vars_from_dispatch(obj, items):
    self.dispatch = add_setters('dispatch', items)(self)



class DumbClass(object):
    def meth(self):
        return 0
    # def eth(self):
        # print("eth-output")

# def append_oy(f):
    # def oy():
        # f()
        # print('oy')
    # return oy


class DumbSubclass(DumbClass):
    def meth(self):
        return add_setters('meth', {'a':1})(self)
    # def eth(self):
        # return append_oy(super().eth)()


ds = DumbSubclass()
ds.meth()
# ds.eth()


import datetime
def jump(increment):
    sign = 1 if increment > 0 else -1
    unit = "months"
    date = datetime.datetime.now() + \
           relativedelta.relativedelta(**{unit:increment})
    return date
