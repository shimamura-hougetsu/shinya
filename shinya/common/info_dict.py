from abc import abstractmethod
from collections import OrderedDict


class InfoDict(OrderedDict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @classmethod
    @abstractmethod
    def from_bytes(cls, data, **kwargs):
        raise NotImplementedError()

    def check_constraints(self):
        if "Length" in self:
            assert self["Length"] == self.calculate_display_size()

    def calculate_display_size(self):
        if "Length" in self:
            return self["Length"]
        else:
            return 0

    def update_counts(self):
        pass

    def update_addresses(self, offset=0):
        pass

    def update_constants(self):
        for key in self.keys():
            if isinstance(self[key], InfoDict):
                self[key].update_constants()
            elif isinstance(self[key], list):
                for item in self[key]:
                    if isinstance(item, InfoDict):
                        item.update_constants()
        self.update_counts()
        if "Length" in self:
            self["Length"] = self.calculate_display_size()

    @abstractmethod
    def to_bytes(self, **kwargs):
        raise NotImplementedError()
