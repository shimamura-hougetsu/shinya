import os

from shinya.bd.extension_data import ExtensionData
from shinya.common.info_dict import InfoDict
from shinya.common.io import unpack_bytes, pack_bytes


class INDXHeader(InfoDict):
    def __init__(self):
        super().__init__()

    @classmethod
    def from_bytes(cls, data, **kwargs):
        self = cls()
        self["TypeIndicator"] = data[0:4].decode("utf-8")
        self["VersionNumber"] = data[4:8].decode("utf-8")
        self["IndexesStartAddress"] = unpack_bytes(data, 8, 4)
        self["ExtensionDataStartAddress"] = unpack_bytes(data, 12, 4)
        self["reserved1"] = data[16:40]

        appinfo_display_size = unpack_bytes(data, 40, 4)
        indexes_display_size = unpack_bytes(data, self["IndexesStartAddress"], 4)

        if self["ExtensionDataStartAddress"]:
            extension_display_size = unpack_bytes(data, self["ExtensionDataStartAddress"], 4)

        assert appinfo_display_size == 34
        assert self["IndexesStartAddress"] == 78
        if self["ExtensionDataStartAddress"]:
            assert (self["IndexesStartAddress"] + indexes_display_size + 4 == self["ExtensionDataStartAddress"])
            assert self["ExtensionDataStartAddress"] + extension_display_size + 4 == len(data)
        else:
            assert self["IndexesStartAddress"] + indexes_display_size + 4 == len(data)

        self["AppInfoBDMV"] = AppInfoBDMV.from_bytes(data[40: 40 + appinfo_display_size + 4])
        self["Indexes"] = Indexes.from_bytes(
            data[self["IndexesStartAddress"]: self["IndexesStartAddress"] + indexes_display_size + 4])
        if self["ExtensionDataStartAddress"]:
            self["ExtensionData"] = ExtensionData.from_bytes(
                data[self["ExtensionDataStartAddress"]: self["ExtensionDataStartAddress"] + extension_display_size + 4],
                self["ExtensionDataStartAddress"])

        assert data == self.to_bytes()
        return self

    def update_addresses(self, offset=0):
        if self["ExtensionDataStartAddress"]:
            self["ExtensionDataStartAddress"] = 40 + self['MovieObjects']['Length'] + 4

    def check_constraints(self):
        assert self["AppInfoBDMV"].calculate_display_size() == 34
        assert self["IndexesStartAddress"] == 78
        if self["ExtensionDataStartAddress"]:
            indexes_display_size = self["Indexes"].calculate_display_size()
            assert (self["IndexesStartAddress"] + indexes_display_size + 4 == self["ExtensionDataStartAddress"])

    def to_bytes(self):
        self.check_constraints()
        data = b""
        data += self["TypeIndicator"].encode("utf-8")
        data += self["VersionNumber"].encode("utf-8")
        data += pack_bytes(self["IndexesStartAddress"], 4)
        data += pack_bytes(self["ExtensionDataStartAddress"], 4)
        data += self["reserved1"]

        data += self["AppInfoBDMV"].to_bytes()
        data += self["Indexes"].to_bytes()
        if self["ExtensionDataStartAddress"]:
            data += self["ExtensionData"].to_bytes(self["ExtensionDataStartAddress"])
        return data


class AppInfoBDMV(InfoDict):
    def __init__(self):
        super().__init__()

    @classmethod
    def from_bytes(cls, data, **kwargs):
        assert len(data) == 38

        self = cls()
        self["Length"] = unpack_bytes(data, 0, 4)
        flags = unpack_bytes(data, 4, 1)
        self["reserved1"] = flags >> 7 & 1
        self["InitialOutputModePreference"] = flags >> 6 & 1
        self["SSContentExistFlag"] = flags >> 5 & 1
        self["reserved2"] = flags >> 4 & 1
        self["InitialDynamicRangeType"] = flags % 2 ** 4
        flags = unpack_bytes(data, 5, 1)
        self["VideoFormat"], self["FrameRate"] = divmod(flags, 2 ** 4)
        self["UserData"] = data[6:]

        return self

    def calculate_display_size(self):
        return 34

    def to_bytes(self):
        self.check_constraints()

        data = b""
        data += pack_bytes(self["Length"], 4)
        flags = (
                (self["reserved1"] << 7)
                + (self["InitialOutputModePreference"] << 6)
                + (self["SSContentExistFlag"] << 5)
                + (self["reserved2"] << 4)
                + self["InitialDynamicRangeType"]
        )
        data += pack_bytes(flags, 1)
        data += pack_bytes((self["VideoFormat"] << 4) + self["FrameRate"], 1)
        data += self["UserData"]

        return data


class Indexes(InfoDict):
    def __init__(self):
        super().__init__()

    @classmethod
    def from_bytes(cls, data, **kwargs):
        self = cls()
        self["Length"] = unpack_bytes(data, 0, 4)
        self["FirstPlaybackTitle"] = Title.from_bytes(data[4:16])
        self["TopMenuTitle"] = Title.from_bytes(data[16:28])
        self["NumberOfTitles"] = unpack_bytes(data, 28, 2)
        self["Titles"] = []
        for i in range(self["NumberOfTitles"]):
            self["Titles"].append(Title.from_bytes(data[30 + i * 12:30 + (i + 1) * 12]))

        return self

    def calculate_display_size(self):
        return 30 + 12 * len(self["Titles"]) - 4

    def update_counts(self):
        self["NumberOfTitles"] = len(self["Titles"])

    def check_constraints(self):
        super().check_constraints()
        assert self["NumberOfTitles"] == len(self["Titles"])

    def to_bytes(self):
        self.check_constraints()

        data = b""
        data += pack_bytes(self["Length"], 4)
        data += self["FirstPlaybackTitle"].to_bytes()
        data += self["TopMenuTitle"].to_bytes()
        data += pack_bytes(self["NumberOfTitles"], 2)
        for i in self["Titles"]:
            data += i.to_bytes()

        return data


class Title(InfoDict):
    def __init__(self):
        super().__init__()

    @classmethod
    def from_bytes(cls, data, **kwargs):
        assert len(data) == 12

        self = cls()
        flags = unpack_bytes(data, 0, 4)
        self["ObjectType"], flags = divmod(flags, 2 ** 30)
        self["AccessType"], self["reserved1"] = divmod(flags, 2 ** 28)
        flags = unpack_bytes(data, 4, 2)
        self["PlaybackType"], self["reserved2"] = divmod(flags, 2 ** 14)

        if self["ObjectType"] == 1:
            self["RefToMovieObjectID"] = unpack_bytes(data, 6, 2)
            self["reserved3"] = unpack_bytes(data, 8, 4)
        else:
            self["RefToBDJObjectID"] = data[6:11].decode("utf-8")
            self["reserved4"] = unpack_bytes(data, 11, 1)

        return self

    def to_bytes(self):
        self.check_constraints()

        data = b""
        data += pack_bytes((self["ObjectType"] << 30) + (self["AccessType"] << 28) + self["reserved1"], 4)
        data += pack_bytes((self["PlaybackType"] << 14) + self["reserved2"], 2)

        if self["ObjectType"] == 1:
            data += pack_bytes(self["RefToMovieObjectID"], 2)
            data += pack_bytes(self["reserved3"], 4)
        else:
            data += self["RefToBDJObjectID"].encode("utf-8")
            data += pack_bytes(self["reserved4"], 1)

        return data


class IndexTableFile:
    def __init__(self, filename=None):
        if not filename:
            self.data = INDXHeader()
        else:
            self.load(filename)

    def load(self, filename):
        with open(filename, "rb") as f:
            data = f.read()
        self.data = INDXHeader.from_bytes(data)

    def save(self, destination, overwrite=False):
        self.data.update_constants()
        self.data.update_addresses()
        if os.path.exists(destination) and not overwrite:
            raise FileExistsError()
        os.makedirs(os.path.dirname(destination), exist_ok=True)
        with open(destination, "wb") as f:
            f.write(self.data.to_bytes())
