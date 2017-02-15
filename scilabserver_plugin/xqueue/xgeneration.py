import json

from xqueue_api.utils import deep_update
from xqueue_api.xobject import XObject


class XGeneration(XObject):

    success = False
    content = ""
    archive_url = None
    grader_payload = None

    def set_generation_result(self, success, content=""):
        self.success = success
        self.content = content
        return self

    def init_api_response(self, api_response):

        parent = super(XGeneration, self)
        if hasattr(parent, 'init_api_response'):
            parent.init_api_response(api_response=api_response)

        body = json.loads(self.body)
        self.archive_url = body.get('archive_64_url')
        self.grader_payload = body.get('grader_payload')

    def prepare_put(self):

        result = {}
        parent = super(XGeneration, self)
        if hasattr(parent, 'prepare_put'):
            result = parent.prepare_put()

        xqueue_body = {
            'success': self.success,
            'content': self.content,
        }

        return deep_update(result, {
            'xqueue_body': xqueue_body,
        })
