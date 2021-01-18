import os

from shinya.bd.extension_data import ExtensionData
from shinya.common.info_dict import InfoDict
from shinya.common.io import unpack_bytes, pack_bytes


class MPLSHeader(InfoDict):
    def __init__(self):
        super().__init__()

    @classmethod
    def from_bytes(cls, data, **kwargs):
        self = cls()
        self["TypeIndicator"] = data[0:4].decode("utf-8")
        self["VersionNumber"] = data[4:8].decode("utf-8")
        self["PlayListStartAddress"] = unpack_bytes(data, 8, 4)
        self["PlayListMarkStartAddress"] = unpack_bytes(data, 12, 4)
        self["ExtensionDataStartAddress"] = unpack_bytes(data, 16, 4)
        self["reserved1"] = data[20:40]

        appinfo_display_size = unpack_bytes(data, 40, 4)
        playlist_display_size = unpack_bytes(data, self["PlayListStartAddress"], 4)
        playlist_mark_display_size = unpack_bytes(data, self["PlayListMarkStartAddress"], 4)

        if self["ExtensionDataStartAddress"]:
            extension_display_size = unpack_bytes(data, self["ExtensionDataStartAddress"], 4)

        assert appinfo_display_size == 14
        assert self["PlayListStartAddress"] == 58
        assert (self["PlayListStartAddress"] + playlist_display_size + 4 == self["PlayListMarkStartAddress"])
        if self["ExtensionDataStartAddress"]:
            assert (self["PlayListMarkStartAddress"] + playlist_mark_display_size + 4 == self[
                "ExtensionDataStartAddress"])
            assert self["ExtensionDataStartAddress"] + extension_display_size + 4 == len(data)
        else:
            assert self["PlayListMarkStartAddress"] + playlist_mark_display_size + 4 == len(data)

        self["AppInfoPlayList"] = AppInfoPlayList.from_bytes(data[40: 40 + appinfo_display_size + 4])
        self["PlayList"] = PlayList.from_bytes(
            data[self["PlayListStartAddress"]: self["PlayListStartAddress"] + playlist_display_size + 4])
        self["PlayListMark"] = PlayListMark.from_bytes(
            data[self["PlayListMarkStartAddress"]: self["PlayListMarkStartAddress"] + playlist_mark_display_size + 4])
        if self["ExtensionDataStartAddress"]:
            self["ExtensionData"] = ExtensionData.from_bytes(
                data[self["ExtensionDataStartAddress"]: self["ExtensionDataStartAddress"] + extension_display_size + 4],
                self["ExtensionDataStartAddress"])

        assert data == self.to_bytes()
        return self

    def update_addresses(self, offset=0):
        playlist_display_size = self["PlayList"].calculate_display_size()
        playlist_mark_display_size = self["PlayListMark"].calculate_display_size()
        self["PlayListMarkStartAddress"] = self["PlayListStartAddress"] + playlist_display_size + 4
        if self["ExtensionDataStartAddress"]:
            self["ExtensionDataStartAddress"] = self["PlayListMarkStartAddress"] + playlist_mark_display_size + 4

    def check_constraints(self):
        appinfo_display_size = self["AppInfoPlayList"].calculate_display_size()
        playlist_display_size = self["PlayList"].calculate_display_size()
        playlist_mark_display_size = self["PlayListMark"].calculate_display_size()

        assert appinfo_display_size == 14
        assert self["PlayListStartAddress"] == 58
        assert (self["PlayListStartAddress"] + playlist_display_size + 4 == self["PlayListMarkStartAddress"])
        if self["ExtensionDataStartAddress"]:
            assert (self["PlayListMarkStartAddress"] + playlist_mark_display_size + 4 == self[
                "ExtensionDataStartAddress"])

    def to_bytes(self):
        self.check_constraints()
        data = b""
        data += self["TypeIndicator"].encode("utf-8")
        data += self["VersionNumber"].encode("utf-8")
        data += pack_bytes(self["PlayListStartAddress"], 4)
        data += pack_bytes(self["PlayListMarkStartAddress"], 4)
        data += pack_bytes(self["ExtensionDataStartAddress"], 4)
        data += self["reserved1"]

        data += self["AppInfoPlayList"].to_bytes()
        data += self["PlayList"].to_bytes()
        data += self["PlayListMark"].to_bytes()
        if self["ExtensionDataStartAddress"]:
            data += self["ExtensionData"].to_bytes(self["ExtensionDataStartAddress"])
        return data


class AppInfoPlayList(InfoDict):
    def __init__(self):
        super().__init__()

    @classmethod
    def from_bytes(cls, data, **kwargs):
        assert len(data) == 18

        self = cls()
        self["Length"] = unpack_bytes(data, 0, 4)
        self["reserved1"] = unpack_bytes(data, 4, 1)
        self["PlaybackType"] = unpack_bytes(data, 5, 1)
        if self["PlaybackType"] in [2, 3]:
            self["PlaybackCount"] = unpack_bytes(data, 6, 2)
        else:
            self["reserved2"] = unpack_bytes(data, 6, 2)

        self["UOMaskTable"] = UOMaskTable.from_bytes(data[8:16])
        flags = unpack_bytes(data, 16, 2)

        self["RandomAccessFlag"] = flags >> 15 & 1
        self["AudioMixFlag"] = flags >> 14 & 1
        self["LosslessBypassFlag"] = flags >> 13 & 1
        self["MVCBaseViewRFlag"] = flags >> 12 & 1
        self["SDRConversionNotificationFlag"] = flags >> 11 & 1
        self["reserved3"] = flags % 2 ** 11

        return self

    def calculate_display_size(self):
        return 14

    def to_bytes(self):

        self.check_constraints()

        flags = (
                (self["RandomAccessFlag"] << 15)
                + (self["AudioMixFlag"] << 14)
                + (self["LosslessBypassFlag"] << 13)
                + (self["MVCBaseViewRFlag"] << 12)
                + (self["SDRConversionNotificationFlag"] << 11)
                + self["reserved3"]
        )

        data = b""
        data += pack_bytes(self["Length"], 4)
        data += pack_bytes(self["reserved1"], 1)
        data += pack_bytes(self["PlaybackType"], 1)

        if self["PlaybackType"] in [2, 3]:
            data += pack_bytes(self["PlaybackCount"], 2)
        else:
            data += pack_bytes(self["reserved2"], 2)

        data += self["UOMaskTable"].to_bytes()
        data += pack_bytes(flags, 2)

        return data


class UOMaskTable(InfoDict):
    def __init__(self):
        super().__init__()

    @classmethod
    def from_bytes(cls, data, **kwargs):
        assert len(data) == 8

        self = cls()
        uo_mask_table = unpack_bytes(data, 0, 8)
        self["MenuCall"] = uo_mask_table >> 63 & 1
        self["TitleSearch"] = uo_mask_table >> 62 & 1
        self["ChapterSearch"] = uo_mask_table >> 61 & 1
        self["TimeSearch"] = uo_mask_table >> 60 & 1
        self["SkipToNextPoint"] = uo_mask_table >> 59 & 1
        self["SkipToPrevPoint"] = uo_mask_table >> 58 & 1
        self["reserved1"] = uo_mask_table >> 57 & 1
        self["Stop"] = uo_mask_table >> 56 & 1
        self["PauseOn"] = uo_mask_table >> 55 & 1
        self["reserved2"] = uo_mask_table >> 54 & 1
        self["StillOff"] = uo_mask_table >> 53 & 1
        self["ForwardPlay"] = uo_mask_table >> 52 & 1
        self["BackwardPlay"] = uo_mask_table >> 51 & 1
        self["Resume"] = uo_mask_table >> 50 & 1
        self["MoveUpSelectedButton"] = uo_mask_table >> 49 & 1
        self["MoveDownSelectedButton"] = uo_mask_table >> 48 & 1
        self["MoveLeftSelectedButton"] = uo_mask_table >> 47 & 1
        self["MoveRightSelectedButton"] = uo_mask_table >> 46 & 1
        self["SelectButton"] = uo_mask_table >> 45 & 1
        self["ActivateButton"] = uo_mask_table >> 44 & 1
        self["SelectAndActivateButton"] = uo_mask_table >> 43 & 1
        self["PrimaryAudioStreamNumberChange"] = uo_mask_table >> 42 & 1
        self["reserved3"] = uo_mask_table >> 41 & 1
        self["AngleNumberChange"] = uo_mask_table >> 40 & 1
        self["PopupOn"] = uo_mask_table >> 39 & 1
        self["PopupOff"] = uo_mask_table >> 38 & 1
        self["PrimaryPGEnableDisable"] = uo_mask_table >> 37 & 1
        self["PrimaryPGStreamNumberChange"] = uo_mask_table >> 36 & 1
        self["SecondaryVideoEnableDisable"] = uo_mask_table >> 35 & 1
        self["SecondaryVideoStreamNumberChange"] = uo_mask_table >> 34 & 1
        self["SecondaryAudioEnableDisable"] = uo_mask_table >> 33 & 1
        self["SecondaryAudioStreamNumberChange"] = uo_mask_table >> 32 & 1
        self["reserved4"] = uo_mask_table >> 31 & 1
        self["SecondaryPGStreamNumberChange"] = uo_mask_table >> 30 & 1
        self["reserved5"] = uo_mask_table % 2 ** 30

        return self

    def to_bytes(self):
        self.check_constraints()

        uo_mask_table = (
                (self["MenuCall"] << 63)
                + (self["TitleSearch"] << 62)
                + (self["ChapterSearch"] << 61)
                + (self["TimeSearch"] << 60)
                + (self["SkipToNextPoint"] << 59)
                + (self["SkipToPrevPoint"] << 58)
                + (self["reserved1"] << 57)
                + (self["Stop"] << 56)
                + (self["PauseOn"] << 55)
                + (self["reserved2"] << 54)
                + (self["StillOff"] << 53)
                + (self["ForwardPlay"] << 52)
                + (self["BackwardPlay"] << 51)
                + (self["Resume"] << 50)
                + (self["MoveUpSelectedButton"] << 49)
                + (self["MoveDownSelectedButton"] << 48)
                + (self["MoveLeftSelectedButton"] << 47)
                + (self["MoveRightSelectedButton"] << 46)
                + (self["SelectButton"] << 45)
                + (self["ActivateButton"] << 44)
                + (self["SelectAndActivateButton"] << 43)
                + (self["PrimaryAudioStreamNumberChange"] << 42)
                + (self["reserved3"] << 41)
                + (self["AngleNumberChange"] << 40)
                + (self["PopupOn"] << 39)
                + (self["PopupOff"] << 38)
                + (self["PrimaryPGEnableDisable"] << 37)
                + (self["PrimaryPGStreamNumberChange"] << 36)
                + (self["SecondaryVideoEnableDisable"] << 35)
                + (self["SecondaryVideoStreamNumberChange"] << 34)
                + (self["SecondaryAudioEnableDisable"] << 33)
                + (self["SecondaryAudioStreamNumberChange"] << 32)
                + (self["reserved4"] << 31)
                + (self["SecondaryPGStreamNumberChange"] << 30)
                + self["reserved5"]
        )

        return pack_bytes(uo_mask_table, 8)


class PlayList(InfoDict):
    def __init__(self):
        super().__init__()

    @classmethod
    def from_bytes(cls, data, **kwargs):

        self = cls()
        self["Length"] = unpack_bytes(data, 0, 4)
        self["reserved1"] = unpack_bytes(data, 4, 2)
        self["NumberOfPlayItems"] = unpack_bytes(data, 6, 2)
        self["NumberOfSubPaths"] = unpack_bytes(data, 8, 2)
        self["PlayItems"] = []
        self["SubPaths"] = []

        read_index = 10
        for i in range(self["NumberOfPlayItems"]):
            item_length = unpack_bytes(data, read_index, 2)
            self["PlayItems"].append(
                PlayItem.from_bytes(data[read_index: read_index + item_length + 2])
            )
            read_index += item_length + 2

        for i in range(self["NumberOfSubPaths"]):
            item_length = unpack_bytes(data, read_index, 4)
            self["SubPaths"].append(
                SubPath.from_bytes(data[read_index: read_index + item_length + 4])
            )
            read_index += item_length + 4

        return self

    def calculate_display_size(self):
        real_length = 10
        for i in self["PlayItems"]:
            real_length += i.calculate_display_size() + 2
        for i in self["SubPaths"]:
            real_length += i.calculate_display_size() + 4
        return real_length - 4

    def update_counts(self):
        self["NumberOfPlayItems"] = len(self["PlayItems"])
        self["NumberOfSubPaths"] = len(self["SubPaths"])

    def check_constraints(self):
        super().check_constraints()
        assert self["NumberOfPlayItems"] == len(self["PlayItems"])
        assert self["NumberOfSubPaths"] == len(self["SubPaths"])

    def to_bytes(self):
        self.check_constraints()
        data = b""
        data += pack_bytes(self["Length"], 4)
        data += pack_bytes(self["reserved1"], 2)
        data += pack_bytes(self["NumberOfPlayItems"], 2)
        data += pack_bytes(self["NumberOfSubPaths"], 2)
        for i in self["PlayItems"]:
            data += i.to_bytes()
        for i in self["SubPaths"]:
            data += i.to_bytes()
        return data


class PlayItem(InfoDict):
    def __init__(self):
        super().__init__()

    @classmethod
    def from_bytes(cls, data, **kwargs):

        self = cls()
        self["Length"] = unpack_bytes(data, 0, 2)
        self["ClipInformationFileName"] = data[2:7].decode("utf-8")
        self["ClipCodecIdentifier"] = data[7:11].decode("utf-8")
        flags = unpack_bytes(data, 11, 2)
        self["reserved1"], flags = divmod(flags, 2 ** 5)
        self["IsMultiAngle"], self["ConnectionCondition"] = divmod(flags, 2 ** 4)
        self["RefToSTCID"] = unpack_bytes(data, 13, 1)
        self["INTime"] = unpack_bytes(data, 14, 4)
        self["OUTTime"] = unpack_bytes(data, 18, 4)
        self["UOMaskTable"] = UOMaskTable.from_bytes(data[22:30])
        flags = unpack_bytes(data, 30, 1)
        self["PlayItemRandomAccessFlag"], self["reserved2"] = divmod(flags, 2 ** 7)
        self["StillMode"] = unpack_bytes(data, 31, 1)
        if self["StillMode"] == 1:
            self["StillTime"] = unpack_bytes(data, 32, 2)
        else:
            self["reserved3"] = unpack_bytes(data, 32, 2)

        read_index = 34

        if self["IsMultiAngle"]:
            self["NumberOfAngles"] = unpack_bytes(data, 34, 1)
            flags = unpack_bytes(data, 35, 1)
            self["reserved4"] = flags // 2 ** 2
            flags %= 2 ** 2
            self["IsDifferentAudios"] = flags // 2
            self["IsSeamlessAngleChange"] = flags % 2
            self["Angles"] = []
            read_index += 2
            for i in range(self["NumberOfAngles"] - 1):
                self["Angles"].append(
                    MultiClipEntry.from_bytes(data[read_index: read_index + 10])
                )
                read_index += 10

        self["STNTable"] = STNTable.from_bytes(data[read_index:])

        return self

    def calculate_display_size(self):
        real_length = 34
        if self["IsMultiAngle"]:
            real_length += 2
            real_length += len(self["Angles"]) * 10
        real_length += self["STNTable"].calculate_display_size() + 2
        return real_length - 2

    def update_counts(self):
        if self["IsMultiAngle"]:
            self["NumberOfAngles"] = len(self["Angles"]) + 1

    def check_constraints(self):
        super().check_constraints()
        if self["IsMultiAngle"]:
            assert self["NumberOfAngles"] - 1 == len(self["Angles"])

    def to_bytes(self):
        self.check_constraints()
        data = b""
        data += pack_bytes(self["Length"], 2)
        data += self["ClipInformationFileName"].encode("utf-8")
        data += self["ClipCodecIdentifier"].encode("utf-8")
        flags = (
                (self["reserved1"] << 5)
                + (self["IsMultiAngle"] << 4)
                + self["ConnectionCondition"]
        )
        data += pack_bytes(flags, 2)
        data += pack_bytes(self["RefToSTCID"], 1)
        data += pack_bytes(self["INTime"], 4)
        data += pack_bytes(self["OUTTime"], 4)
        data += self["UOMaskTable"].to_bytes()
        data += pack_bytes(
            (self["PlayItemRandomAccessFlag"] << 7) + self["reserved2"], 1
        )
        data += pack_bytes(self["StillMode"], 1)
        if self["StillMode"] == 1:
            data += pack_bytes(self["StillTime"], 2)
        else:
            data += pack_bytes(self["reserved3"], 2)

        if self["IsMultiAngle"]:
            data += pack_bytes(self["NumberOfAngles"], 1)
            data += pack_bytes(
                (self["reserved4"] << 2)
                + (self["IsDifferentAudios"] << 1)
                + self["IsSeamlessAngleChange"],
                1
            )
            for i in self["Angles"]:
                data += i.to_bytes()

        data += self["STNTable"].to_bytes()

        return data


class STNTable(InfoDict):
    stream_names = [
        "PrimaryVideoStreamEntries",
        "PrimaryAudioStreamEntries",
        "PrimaryPGStreamEntries",
        "PrimaryIGStreamEntries",
        "SecondaryAudioStreamEntries",
        "SecondaryVideoStreamEntries",
        "SecondaryPGStreamEntries",
        "DVStreamEntries",
    ]

    def __init__(self):
        super().__init__()

    @classmethod
    def from_bytes(cls, data, **kwargs):

        self = cls()
        self["Length"] = unpack_bytes(data, 0, 2)
        if self["Length"] != 0:
            self["reserved1"] = unpack_bytes(data, 2, 2)

            read_index = 4
            for name in self.stream_names:
                self[f"NumberOf{name}"] = unpack_bytes(data, read_index, 1)
                read_index += 1

            self["reserved2"] = unpack_bytes(data, 12, 4)
            read_index = 16

            for name in self.stream_names:
                self[name] = []
                for i in range(self[f"NumberOf{name}"]):
                    info_pair = InfoDict()

                    stream_entry_length = unpack_bytes(data, read_index, 1)
                    info_pair["StreamEntry"] = StreamEntry.from_bytes(
                        data[read_index: read_index + stream_entry_length + 1]
                    )
                    read_index += stream_entry_length + 1

                    stream_attr_length = unpack_bytes(data, read_index, 1)
                    info_pair["StreamAttributes"] = StreamAttributes.from_bytes(
                        data[read_index: read_index + stream_attr_length + 1]
                    )
                    read_index += stream_attr_length + 1

                    self[name].append(info_pair)

        return self

    def calculate_display_size(self):
        if self["Length"] != 0:
            real_length = 16
            for name in self.stream_names:
                for i in self[name]:
                    real_length += (
                            i["StreamEntry"].calculate_display_size() + 1
                            + i["StreamAttributes"].calculate_display_size() + 1
                    )
            return real_length - 2
        else:
            return 0

    def update_counts(self):
        if self["Length"] != 0:
            for name in self.stream_names:
                self[f"NumberOf{name}"] = len(self[name])

    def check_constraints(self):
        super().check_constraints()
        if self["Length"] != 0:
            for name in self.stream_names:
                assert self[f"NumberOf{name}"] == len(self[name])

    def to_bytes(self):
        self.check_constraints()
        data = b""
        data += pack_bytes(self["Length"], 2)
        if self["Length"] != 0:
            data += pack_bytes(self["reserved1"], 2)
            for name in self.stream_names:
                data += pack_bytes(self[f"NumberOf{name}"], 1)
            data += pack_bytes(self["reserved2"], 4)
            for name in self.stream_names:
                for i in self[name]:
                    data += i["StreamEntry"].to_bytes()
                    data += i["StreamAttributes"].to_bytes()
        return data


class StreamEntry(InfoDict):
    def __init__(self):
        super().__init__()

    @classmethod
    def from_bytes(cls, data, **kwargs):
        self = cls()
        self["Length"] = unpack_bytes(data, 0, 1)
        if self["Length"] != 0:
            self["StreamType"] = unpack_bytes(data, 1, 1)
            if self["StreamType"] == 1:
                self["RefToStreamPID"] = unpack_bytes(data, 2, 2)
            elif self["StreamType"] == 2:
                self["RefToSubPathID"] = unpack_bytes(data, 2, 1)
                self["RefToSubClipID"] = unpack_bytes(data, 3, 1)
                self["RefToStreamPID"] = unpack_bytes(data, 4, 2)
            elif self["StreamType"] in [3, 4]:
                self["RefToSubPathID"] = unpack_bytes(data, 2, 1)
                self["RefToStreamPID"] = unpack_bytes(data, 3, 2)
            else:
                assert False

        return self

    def calculate_display_size(self):
        if self["Length"] != 0:
            return 9
        else:
            return 0

    # def check_constraints(self):
    #     if self["Length"] != 0:
    #         self["Length"] + 1 == 10
    #
    #         if self["StreamType"] == 1:
    #             assert self["Length"] + 1 == 4
    #         elif self["StreamType"] == 2:
    #             assert self["Length"] + 1 == 6
    #         elif self["StreamType"] in [3, 4]:
    #             assert self["Length"] + 1 == 5
    #         else:
    #             assert False

    def to_bytes(self):
        self.check_constraints()
        data = b""
        data += pack_bytes(self["Length"], 1)
        if self["Length"] != 0:
            data += pack_bytes(self["StreamType"], 1)
            if self["StreamType"] == 1:
                data += pack_bytes(self["RefToStreamPID"], 2)
                data += b"\x00\x00\x00\x00\x00\x00"
            elif self["StreamType"] == 2:
                data += pack_bytes(self["RefToSubPathID"], 1)
                data += pack_bytes(self["RefToSubClipID"], 1)
                data += pack_bytes(self["RefToStreamPID"], 2)
                data += b"\x00\x00\x00\x00"
            elif self["StreamType"] in [3, 4]:
                data += pack_bytes(self["RefToSubPathID"], 1)
                data += pack_bytes(self["RefToStreamPID"], 2)
                data += b"\x00\x00\x00\x00\x00"
            return data


class StreamAttributes(InfoDict):
    def __init__(self):
        super().__init__()

    @classmethod
    def from_bytes(cls, data, **kwargs):

        self = cls()
        self["Length"] = unpack_bytes(data, 0, 1)
        if self["Length"] != 0:
            self["StreamCodingType"] = unpack_bytes(data, 1, 1)
            if self["StreamCodingType"] in [0x01, 0x02, 0x1B, 0xEA]:
                tmp = unpack_bytes(data, 2, 1)
                self["VideoFormat"], self["FrameRate"] = divmod(tmp, 2 ** 4)

            elif self["StreamCodingType"] == 0x24:
                tmp = unpack_bytes(data, 2, 1)
                self["VideoFormat"], self["FrameRate"] = divmod(tmp, 2 ** 4)
                tmp = unpack_bytes(data, 3, 1)
                self["DynamicRangeType"], self["ColorSpace"] = divmod(tmp, 2 ** 4)
                tmp = unpack_bytes(data, 4, 1)
                self["CRFlag"] = tmp >> 7 & 1
                self["HDRPlusFlag"] = tmp >> 6 & 1

            elif self["StreamCodingType"] in [0x03, 0x04, 0x80, 0x81, 0x82, 0x83, 0x84, 0x85, 0x86, 0xA1, 0xA2]:
                tmp = unpack_bytes(data, 2, 1)
                self["AudioFormat"], self["SampleRate"] = divmod(tmp, 2 ** 4)
                self["LanguageCode"] = data[3:6].decode("utf-8")

            elif self["StreamCodingType"] in [0x90, 0x91]:
                self["LanguageCode"] = data[2:5].decode("utf-8")

            elif self["StreamCodingType"] in [0x92]:
                self["CharacterCode"] = unpack_bytes(data, 2, 1)
                self["LanguageCode"] = data[3:6].decode("utf-8")

            else:
                assert False

        return self

    def calculate_display_size(self):
        if self["Length"] != 0:
            return 5
        else:
            return 0

    #     def check_constraints(self):
    #         if self["Length"] != 0:
    #             assert self["Length"] + 1 == 6

    #             if self["StreamCodingType"] in [0x01, 0x02, 0x1B, 0xEA]:
    #                 assert self["Length"] + 1 == 3

    #             elif self["StreamCodingType"] == 0x24:
    #                 assert self["Length"] + 1 == 5

    #             elif self["StreamCodingType"] in [
    #                 0x03,
    #                 0x04,
    #                 0x80,
    #                 0x81,
    #                 0x82,
    #                 0x83,
    #                 0x84,
    #                 0x85,
    #                 0x86,
    #                 0xA1,
    #                 0xA2,
    #             ]:
    #                 assert self["Length"] + 1 == 6

    #             elif self["StreamCodingType"] in [0x90, 0x91]:
    #                 assert self["Length"] + 1 == 5

    #             elif self["StreamCodingType"] in [0x92]:
    #                 assert self["Length"] + 1 == 6

    #             else:
    #                 assert False

    def to_bytes(self):
        self.check_constraints()
        data = b""
        data += pack_bytes(self["Length"], 1)
        if self["Length"] != 0:
            data += pack_bytes(self["StreamCodingType"], 1)
            if self["StreamCodingType"] in [0x01, 0x02, 0x1B, 0xEA]:
                data += pack_bytes(
                    (self["VideoFormat"] << 4) + self["FrameRate"], 1
                )
                data += b"\x00\x00\x00"

            elif self["StreamCodingType"] == 0x24:
                data += pack_bytes(
                    (self["VideoFormat"] << 4) + self["FrameRate"], 1
                )
                data += pack_bytes(
                    (self["DynamicRangeType"] << 4) + self["ColorSpace"], 1
                )
                data += pack_bytes(
                    (self["CRFlag"] << 7) + (self["HDRPlusFlag"] << 6), 1
                )
                data += b"\x00"

            elif self["StreamCodingType"] in [0x03, 0x04, 0x80, 0x81, 0x82, 0x83, 0x84, 0x85, 0x86, 0xA1, 0xA2]:
                data += pack_bytes(
                    (self["AudioFormat"] << 4) + self["SampleRate"], 1
                )
                data += self["LanguageCode"].encode("utf-8")

            elif self["StreamCodingType"] in [0x90, 0x91]:
                data += self["LanguageCode"].encode("utf-8")
                data += b"\x00"

            elif self["StreamCodingType"] in [0x92]:
                data += pack_bytes(self["CharacterCode"], 1)
                data += self["LanguageCode"].encode("utf-8")

        return data


class SubPath(InfoDict):
    def __init__(self):
        super().__init__()

    @classmethod
    def from_bytes(cls, data, **kwargs):

        self = cls()
        self["Length"] = unpack_bytes(data, 0, 4)
        self["reserved1"] = unpack_bytes(data, 4, 1)
        self["SubPathType"] = unpack_bytes(data, 5, 1)
        flags = unpack_bytes(data, 6, 2)
        self["reserved2"] = flags // 2
        self["IsRepeatSubPath"] = flags % 2
        self["reserved3"] = unpack_bytes(data, 8, 1)
        self["NumberOfSubPlayItems"] = unpack_bytes(data, 9, 1)
        self["SubPlayItems"] = []
        read_index = 10
        for i in range(self["NumberOfSubPlayItems"]):
            item_length = unpack_bytes(data, read_index, 2)
            self["SubPlayItems"].append(SubPlayItem.from_bytes(data[read_index: read_index + item_length + 2]))
            read_index += item_length + 2

        return self

    def calculate_display_size(self):
        real_length = 10
        for i in self["SubPlayItems"]:
            real_length += i.calculate_display_size() + 2
        return real_length - 4

    def update_counts(self):
        self["NumberOfSubPlayItems"] = len(self["SubPlayItems"])

    def check_constraints(self):
        super().check_constraints()
        assert self["NumberOfSubPlayItems"] == len(self["SubPlayItems"])

    def to_bytes(self):
        self.check_constraints()
        data = b""
        data += pack_bytes(self["Length"], 4)
        data += pack_bytes(self["reserved1"], 1)
        data += pack_bytes(self["SubPathType"], 1)
        data += pack_bytes(self["reserved2"] * 2 + self["IsRepeatSubPath"], 2)
        data += pack_bytes(self["reserved3"], 1)
        data += pack_bytes(self["NumberOfSubPlayItems"], 1)
        for i in self["SubPlayItems"]:
            data += i.to_bytes()
        return data


class SubPlayItem(InfoDict):
    def __init__(self):
        super().__init__()

    @classmethod
    def from_bytes(cls, data, **kwargs):
        self = cls()
        self["Length"] = unpack_bytes(data, 0, 2)
        self["ClipInformationFileName"] = data[2:7].decode("utf-8")
        self["ClipCodecIdentifier"] = data[7:11].decode("utf-8")
        flags = unpack_bytes(data, 11, 4)
        self["reserved1"], flags = divmod(flags, 2 ** 5)
        self["ConnectionCondition"], self["IsMultiClipEntries"] = divmod(flags, 2)
        self["RefToSTCID"] = unpack_bytes(data, 15, 1)
        self["INTime"] = unpack_bytes(data, 16, 4)
        self["OUTTime"] = unpack_bytes(data, 20, 4)
        self["SyncPlayItemID"] = unpack_bytes(data, 24, 2)
        self["SyncStartPTS"] = unpack_bytes(data, 26, 4)

        if self["IsMultiClipEntries"]:
            self["NumberOfMultiClipEntries"] = unpack_bytes(data, 30, 1)
            self["reserved2"] = unpack_bytes(data, 31, 1)
            self["MultiClipEntries"] = []
            for i in range(self["NumberOfMultiClipEntries"]):
                self["MultiClipEntries"].append(MultiClipEntry.from_bytes(data[32 + 10 * i: 32 + 10 * (i + 1)]))

        return self

    def calculate_display_size(self):
        if self["IsMultiClipEntries"]:
            return 32 + len(self["MultiClipEntries"]) * 10 - 2
        else:
            return 30 - 2

    def update_counts(self):
        if self["IsMultiClipEntries"]:
            self["NumberOfMultiClipEntries"] = len(self["MultiClipEntries"])

    def check_constraints(self):
        super().check_constraints()
        if self["IsMultiClipEntries"]:
            assert self["NumberOfMultiClipEntries"] == len(self["MultiClipEntries"])

    def to_bytes(self):
        self.check_constraints()

        data = b""
        data += pack_bytes(self["Length"], 2)
        data += self["ClipInformationFileName"].encode("utf-8")
        data += self["ClipCodecIdentifier"].encode("utf-8")
        flags = (
                (self["reserved1"] << 5)
                + (self["ConnectionCondition"] << 1)
                + self["IsMultiClipEntries"]
        )
        data += pack_bytes(flags, 4)
        data += pack_bytes(self["RefToSTCID"], 1)
        data += pack_bytes(self["INTime"], 4)
        data += pack_bytes(self["OUTTime"], 4)
        data += pack_bytes(self["SyncPlayItemID"], 2)
        data += pack_bytes(self["SyncStartPTS"], 4)

        if self["IsMultiClipEntries"]:
            data += pack_bytes(self["NumberOfMultiClipEntries"], 1)
            data += pack_bytes(self["reserved2"], 1)
            for i in self["MultiClipEntries"]:
                data += i.to_bytes()
        return data


class MultiClipEntry(InfoDict):
    def __init__(self):
        super().__init__()

    @classmethod
    def from_bytes(cls, data, **kwargs):
        assert len(data) == 10
        self = cls()
        self["ClipInformationFileName"] = data[0:5].decode("utf-8")
        self["ClipCodecIdentifier"] = data[5:9].decode("utf-8")
        self["RefToSTCID"] = unpack_bytes(data, 9, 1)
        return self

    def to_bytes(self):
        self.check_constraints()

        data = b""
        data += self["ClipInformationFileName"].encode("utf-8")
        data += self["ClipCodecIdentifier"].encode("utf-8")
        data += pack_bytes(self["RefToSTCID"], 1)

        return data


class PlayListMark(InfoDict):
    def __init__(self):
        super().__init__()

    @classmethod
    def from_bytes(cls, data, **kwargs):
        self = cls()
        self["Length"] = unpack_bytes(data, 0, 4)
        self["NumberOfPlayListMarks"] = unpack_bytes(data, 4, 2)
        self["PlayListMarks"] = []
        for i in range(self["NumberOfPlayListMarks"]):
            self["PlayListMarks"].append(PlayListMarkItem.from_bytes(data[6 + 14 * i: 6 + 14 * (i + 1)]))
        return self

    def calculate_display_size(self):
        return self["NumberOfPlayListMarks"] * 14 + 2

    def update_counts(self):
        self["NumberOfPlayListMarks"] = len(self["PlayListMarks"])

    def check_constraints(self):
        super().check_constraints()
        assert self["NumberOfPlayListMarks"] == len(self["PlayListMarks"])

    def to_bytes(self):
        self.check_constraints()
        data = b""
        data += pack_bytes(self["Length"], 4)
        data += pack_bytes(self["NumberOfPlayListMarks"], 2)
        for i in self["PlayListMarks"]:
            data += i.to_bytes()
        return data


class PlayListMarkItem(InfoDict):
    def __init__(self):
        super().__init__()

    @classmethod
    def from_bytes(cls, data, **kwargs):
        assert len(data) == 14
        self = cls()
        self["reserved1"] = unpack_bytes(data, 0, 1)
        self["MarkType"] = unpack_bytes(data, 1, 1)
        self["RefToPlayItemID"] = unpack_bytes(data, 2, 2)
        self["MarkTimeStamp"] = unpack_bytes(data, 4, 4)
        self["EntryESPID"] = unpack_bytes(data, 8, 2)
        self["Duration"] = unpack_bytes(data, 10, 4)

        return self

    def to_bytes(self):
        self.check_constraints()
        data = b""
        data += pack_bytes(self["reserved1"], 1)
        data += pack_bytes(self["MarkType"], 1)
        data += pack_bytes(self["RefToPlayItemID"], 2)
        data += pack_bytes(self["MarkTimeStamp"], 4)
        data += pack_bytes(self["EntryESPID"], 2)
        data += pack_bytes(self["Duration"], 4)
        return data


class MoviePlaylist:
    def __init__(self, filename=None):
        if not filename:
            self.data = MPLSHeader()
        else:
            self.load(filename)

    def load(self, filename):
        with open(filename, "rb") as f:
            data = f.read()
        self.data = MPLSHeader.from_bytes(data)

    def save(self, destination, overwrite=False):
        self.data.update_constants()
        self.data.update_addresses()
        if os.path.exists(destination) and not overwrite:
            raise FileExistsError()
        os.makedirs(os.path.dirname(destination), exist_ok=True)
        with open(destination, "wb") as f:
            f.write(self.data.to_bytes())
