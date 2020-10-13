import functools
import logging

from xqueue_api.xsubmission import XSubmission

from .configuration import IfmoXBServerConfiguration

logger = logging.getLogger(__name__)


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
        key = (self.__class__.__name__, event)
        if key in self.events:
            try:
                return self.events[key](self, xobject=xobject)
            except Exception as e:  # noqa
                logger.exception('Failed to handle submission')
                error_sub = XSubmission(xobject=xobject)
                error_sub.set_grade(grade=0, feedback='Не удалось проверить решение', correctness=False, success=False)
                return str(e)

        else:
            msg = "Unknown method for %s plugin: %s" % (self.__class__.__name__, event)
            error_sub = XSubmission(xobject=xobject)
            error_sub.set_grade(grade=0, feedback=msg, correctness=False, success=False)
            return error_sub

    @classmethod
    def register_method(cls, class_name, event):
        def handle(m):
            cls.events[(class_name, event)] = m
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
