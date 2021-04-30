from shinya.common.info_dict import InfoDict
from shinya.common.io import unpack_bytes, pack_bytes


class ExtensionData(InfoDict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @classmethod
    def from_bytes(cls, data, **kwargs):
        self = cls()
        self["Length"] = unpack_bytes(data, 0, 4)
        if self["Length"]:
            # libbluray ignores this address and use the ones below
            self["DataBlockStartAddress"] = unpack_bytes(data, 4, 4)
            self["reserved1"] = unpack_bytes(data, 8, 2)
            self["reserved2"] = unpack_bytes(data, 10, 1)
            self["NumberOfExtDataEntries"] = unpack_bytes(data, 11, 1)
            self["ExtDataEntryInfo"] = []
            self["ExtDataEntry"] = []
            # starts at offset 12, each info block contains 12 bytes
            for i in range(self["NumberOfExtDataEntries"]):
                extdata_entry_info = InfoDict()
                extdata_entry_info["ExtDataType"] = unpack_bytes(data, 12 + 12 * i, 2)
                extdata_entry_info["ExtDataVersion"] = unpack_bytes(data, 12 + 12 * i + 2, 2)
                extdata_entry_info["ExtDataStartAddress"] = unpack_bytes(data, 12 + 12 * i + 4, 4)
                extdata_entry_info["ExtDataLength"] = unpack_bytes(data, 12 + 12 * i + 8, 4)
                self["ExtDataEntryInfo"].append(extdata_entry_info)
                self["ExtDataEntry"].append(ExtDataEntry.from_bytes(data[extdata_entry_info["ExtDataStartAddress"]:
                                                                         extdata_entry_info["ExtDataStartAddress"] +
                                                                         extdata_entry_info["ExtDataLength"]]))
        return self

    def calculate_display_size(self):
        if self["Length"]:
            real_length = 12 + 12 * len(self["ExtDataEntryInfo"])
            for ext_data in self["ExtDataEntry"]:
                real_length += ext_data.calculate_display_size()
            return real_length - 4
        else:
            return 0

    def check_constraints(self):
        if self["Length"]:
            assert self["NumberOfExtDataEntries"] == len(self["ExtDataEntryInfo"])
            assert self["NumberOfExtDataEntries"] == len(self["ExtDataEntry"])
            for ext_data_info, ext_data in zip(self["ExtDataEntryInfo"], self["ExtDataEntry"]):
                assert ext_data_info["ExtDataLength"] == ext_data.calculate_display_size()
            if len(self["ExtDataEntryInfo"]):
                assert self["ExtDataEntryInfo"][0]["ExtDataStartAddress"] == self["DataBlockStartAddress"]

    def to_bytes(self):
        self.check_constraints()
        data = b""
        data += pack_bytes(self["Length"], 4)
        if self["Length"]:
            data += pack_bytes(self["DataBlockStartAddress"], 4)
            data += pack_bytes(self["reserved1"], 2)
            data += pack_bytes(self["reserved2"], 1)
            data += pack_bytes(self["NumberOfExtDataEntries"], 1)
            for ext_data_info in self["ExtDataEntryInfo"]:
                data += pack_bytes(ext_data_info["ExtDataType"], 2)
                data += pack_bytes(ext_data_info["ExtDataVersion"], 2)
                data += pack_bytes(ext_data_info["ExtDataStartAddress"], 4)
                data += pack_bytes(ext_data_info["ExtDataLength"], 4)
            for ext_data in self["ExtDataEntry"]:
                data += ext_data.to_bytes()
        return data


class ExtDataEntry(InfoDict):
    """ Extension data entry is class and type specific, and is not implemented yet
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @classmethod
    def from_bytes(cls, data, **kwargs):
        self = cls()
        self["data"] = data
        return self

    def calculate_display_size(self):
        return len(self["data"])

    def to_bytes(self, **kwargs):
        return self["data"]
