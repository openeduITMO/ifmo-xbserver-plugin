class IfmoXBServerConfiguration(object):

    required_fields = ()
    data = {}

    def __setattr__(self, key, value):
        self.data[key] = value
        
    def __getattribute__(self, item):
        data = super(IfmoXBServerConfiguration, self).__getattribute__("data")
        return data.get(item, super(IfmoXBServerConfiguration, self).__getattribute__(item))

    def __getattr__(self, item):
        # Since we check in data dict prior to instance/parent dict, 
        # we need to check this field in requirement whether to raise AttributeError
        if item not in super(IfmoXBServerConfiguration, self).__getattribute__("required_fields"):
            return None
        else:
            raise AttributeError(item)

    def update(self, configuration):
        self.data.update(configuration)
