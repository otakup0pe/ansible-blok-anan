from ansible import errors

import os.path

class FilterModule(object):
    filter_map = {
        'basename': os.path.basename
    }

    def filters(self):
        return self.filter_map
