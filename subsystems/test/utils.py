class ContextTest(object):
    def __init__(self):
        self.context = {
            "out": []
        }

    def out(self, key, value):
        self.context["out"].append((key, value))
        return self

    def dict(self):
        return self.context