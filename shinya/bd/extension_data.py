from shinya.common.info_dict import InfoDict


class ExtensionData(InfoDict):
    def __init__(self):
        super().__init__()

    @classmethod
    def from_bytes(cls, data, address=0):
        raise NotImplementedError()

    def check_constraints(self):
        raise NotImplementedError()

    def to_bytes(self, address=0):
        raise NotImplementedError()
