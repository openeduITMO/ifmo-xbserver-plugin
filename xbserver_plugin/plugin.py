import functools

from xqueue_api.xsubmission import XSubmission

from .configuration import IfmoXBServerConfiguration


class IfmoXBServerPlugin(object):

    events = {}
    configuration_section = None
    configuration = {}

    def __init__(self, configuration=None):

        if configuration is None:
            self.configuration = IfmoXBServerConfiguration()
        else:
            self.configuration.update(configuration)

    def handle(self, event, xobject=None):
        if event in self.events:
            return self.events[event](self, xobject=xobject)
        else:
            msg = "Unknown method for %s plugin: %s" % (self.__class__.__name__, event)
            error_sub = XSubmission(xobject=xobject)
            error_sub.set_grade(grade=0, feedback=msg, correctness=False, success=False)
            return error_sub

    @classmethod
    def register_method(cls, event):
        def handle(m):
            cls.events[event] = m
            return m
        return handle

    @classmethod
    def want_xobject(cls, clz):
        """
        Declare what kind of xobject handler wants.

        :param clz: Class of XObject
        :return:
        """
        def handle(m):
            @functools.wraps(m)
            def inner(*args, **kwargs):
                kwargs.update({'xobject': clz(xobject=kwargs.get('xobject'))})
                return m(*args, **kwargs)
            return inner
        return handle

    @classmethod
    def register_default_config(cls, config_cls):
        def handle(clz):
            clz.configuration = config_cls()
            return clz
        return handle