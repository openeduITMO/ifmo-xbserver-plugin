class IfmoXBServerConfiguration(object):

    required_fields = ()
    data = {}

    def __setattr__(self, key, value):
        self.data[key] = value

    def __getattr__(self, item):
        try:
            return self.data.get(item, getattr(self, item))
        except KeyError:
            if item not in self.required_fields:
                return None
            else:
                raise

    def update(self, configuration):
        self.data.update(configuration)
