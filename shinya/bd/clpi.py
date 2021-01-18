import os

from shinya.bd.extension_data import ExtensionData
from shinya.common.info_dict import InfoDict
from shinya.common.io import unpack_bytes, pack_bytes


class CLPIHeader(InfoDict):
    def __init__(self):
        super().__init__()

    @classmethod
    def from_bytes(cls, data, **kwargs):
        self = cls()
        self["TypeIndicator"] = data[0:4].decode("utf-8")
        self["VersionNumber"] = data[4:8].decode("utf-8")
        self["SequenceInfoStartAddress"] = unpack_bytes(data, 8, 4)
        self["ProgramInfoStartAddress"] = unpack_bytes(data, 12, 4)
        self["CPIStartAddress"] = unpack_bytes(data, 16, 4)
        self["ClipMarkStartAddress"] = unpack_bytes(data, 20, 4)
        self["ExtensionDataStartAddress"] = unpack_bytes(data, 24, 4)
        self["reserved1"] = data[28:40]

        clip_info_display_size = unpack_bytes(data, 40, 4)
        sequence_info_display_size = unpack_bytes(data, self["SequenceInfoStartAddress"], 4)
        program_info_display_size = unpack_bytes(data, self["ProgramInfoStartAddress"], 4)
        cpi_display_size = unpack_bytes(data, self["CPIStartAddress"], 4)
        clip_mark_display_size = unpack_bytes(data, self["ClipMarkStartAddress"], 4)

        if self["ExtensionDataStartAddress"]:
            extension_display_size = unpack_bytes(data, self["ExtensionDataStartAddress"], 4)

        assert 40 + clip_info_display_size + 4 == self["SequenceInfoStartAddress"]
        assert self["SequenceInfoStartAddress"] + sequence_info_display_size + 4 == self["ProgramInfoStartAddress"]
        assert self["ProgramInfoStartAddress"] + program_info_display_size + 4 == self["CPIStartAddress"]
        assert self["CPIStartAddress"] + cpi_display_size + 4 == self["ClipMarkStartAddress"]

        if self["ExtensionDataStartAddress"]:
            assert self["ClipMarkStartAddress"] + clip_mark_display_size + 4 == self["ExtensionDataStartAddress"]
            assert self["ExtensionDataStartAddress"] + extension_display_size + 4 == len(data)
        else:
            assert self["ClipMarkStartAddress"] + clip_mark_display_size + 4 == len(data)

        self["ClipInfo"] = ClipInfo.from_bytes(data[40: 40 + clip_info_display_size + 4])
        self["SequenceInfo"] = SequenceInfo.from_bytes(
            data[self["SequenceInfoStartAddress"]: self["SequenceInfoStartAddress"] + sequence_info_display_size + 4])
        self["ProgramInfo"] = ProgramInfo.from_bytes(
            data[self["ProgramInfoStartAddress"]: self["ProgramInfoStartAddress"] + program_info_display_size + 4])
        self["CPI"] = CPI.from_bytes(data[self["CPIStartAddress"]: self["CPIStartAddress"] + cpi_display_size + 4])
        self["ClipMark"] = ClipMark.from_bytes(
            data[self["ClipMarkStartAddress"]:self["ClipMarkStartAddress"] + clip_mark_display_size + 4])
        if self["ExtensionDataStartAddress"]:
            self["ExtensionData"] = ExtensionData.from_bytes(
                data[self["ExtensionDataStartAddress"]: self["ExtensionDataStartAddress"] + extension_display_size + 4],
                self["ExtensionDataStartAddress"])

        assert data == self.to_bytes()
        return self

    def update_addresses(self, offset=0):
        clip_info_display_size = self["ClipInfo"].calculate_display_size()
        sequence_info_display_size = self["SequenceInfo"].calculate_display_size()
        program_info_display_size = self["ProgramInfo"].calculate_display_size()
        cpi_display_size = self["CPI"].calculate_display_size()
        clip_mark_display_size = self["ClipMark"].calculate_display_size()
        self["SequenceInfoStartAddress"] = 40 + clip_info_display_size + 4
        self["ProgramInfoStartAddress"] = self["SequenceInfoStartAddress"] + sequence_info_display_size + 4
        self["CPIStartAddress"] = self["ProgramInfoStartAddress"] + program_info_display_size + 4
        self["ClipMarkStartAddress"] = self["CPIStartAddress"] + cpi_display_size + 4
        if self["ExtensionDataStartAddress"]:
            self["ExtensionDataStartAddress"] = self["ClipMarkStartAddress"] + clip_mark_display_size + 4
        pass

    def check_constraints(self):
        clip_info_display_size = self["ClipInfo"].calculate_display_size()
        sequence_info_display_size = self["SequenceInfo"].calculate_display_size()
        program_info_display_size = self["ProgramInfo"].calculate_display_size()
        cpi_display_size = self["CPI"].calculate_display_size()
        clip_mark_display_size = self["ClipMark"].calculate_display_size()
        assert 40 + clip_info_display_size + 4 == self["SequenceInfoStartAddress"]
        assert self["SequenceInfoStartAddress"] + sequence_info_display_size + 4 == self["ProgramInfoStartAddress"]
        assert self["ProgramInfoStartAddress"] + program_info_display_size + 4 == self["CPIStartAddress"]
        assert self["CPIStartAddress"] + cpi_display_size + 4 == self["ClipMarkStartAddress"]
        if self["ExtensionDataStartAddress"]:
            assert self["ClipMarkStartAddress"] + clip_mark_display_size + 4 == self["ExtensionDataStartAddress"]

    def to_bytes(self):
        self.check_constraints()
        data = b""
        data += self["TypeIndicator"].encode("utf-8")
        data += self["VersionNumber"].encode("utf-8")
        data += pack_bytes(self["SequenceInfoStartAddress"], 4)
        data += pack_bytes(self["ProgramInfoStartAddress"], 4)
        data += pack_bytes(self["CPIStartAddress"], 4)
        data += pack_bytes(self["ClipMarkStartAddress"], 4)
        data += pack_bytes(self["ExtensionDataStartAddress"], 4)
        data += self["reserved1"]

        data += self["ClipInfo"].to_bytes()
        data += self["SequenceInfo"].to_bytes()
        data += self["ProgramInfo"].to_bytes()
        data += self["CPI"].to_bytes()
        data += self["ClipMark"].to_bytes()
        if self["ExtensionDataStartAddress"]:
            data += self["ExtensionData"].to_bytes(self["ExtensionDataStartAddress"])
        return data


class ClipInfo(InfoDict):
    def __init__(self):
        super().__init__()

    @classmethod
    def from_bytes(cls, data, **kwargs):
        self = cls()
        self["Length"] = unpack_bytes(data, 0, 4)
        self["reserved1"] = unpack_bytes(data, 4, 2)
        self["ClipStreamType"] = unpack_bytes(data, 6, 1)
        self["ApplicationType"] = unpack_bytes(data, 7, 1)
        flags = unpack_bytes(data, 8, 4)
        self["reserved2"], self["IsCC5"] = divmod(flags, 2)
        self["TSRecordingRate"] = unpack_bytes(data, 12, 4)
        self["NumberOfSourcePackets"] = unpack_bytes(data, 16, 4)
        self["reserved3"] = data[20:148]
        self["TSTypeInfoBlock"] = TSTypeInfoBlock.from_bytes(data[148:180])
        if self["IsCC5"]:
            self["reserved4"] = unpack_bytes(data, 180, 1)
            self["FollowingClipStreamType"] = unpack_bytes(data, 181, 1)
            self["reserved5"] = unpack_bytes(data, 182, 4)
            self["FollowingClipInformationFileName"] = data[186:191].decode("utf-8")
            self["FollowingClipCodecIdentifier"] = data[191:195].decode("utf-8")
            self["reserved6"] = unpack_bytes(data, 195, 1)
        return self

    def calculate_display_size(self):
        if self["IsCC5"]:
            return 196 - 4
        else:
            return 180 - 4

    def to_bytes(self):
        self.check_constraints()
        data = b""
        data += pack_bytes(self["Length"], 4)
        data += pack_bytes(self["reserved1"], 2)
        data += pack_bytes(self["ClipStreamType"], 1)
        data += pack_bytes(self["ApplicationType"], 1)
        data += pack_bytes(self["reserved2"] * 2 + self["IsCC5"], 4)
        data += pack_bytes(self["TSRecordingRate"], 4)
        data += pack_bytes(self["NumberOfSourcePackets"], 4)
        data += self["reserved3"]
        data += self["TSTypeInfoBlock"].to_bytes()
        if self["IsCC5"]:
            data += pack_bytes(self["reserved4"], 1)
            data += pack_bytes(self["FollowingClipStreamType"], 1)
            data += pack_bytes(self["reserved5"], 4)
            data += self["FollowingClipInformationFileName"].encode("utf-8")
            data += self["FollowingClipCodecIdentifier"].encode("utf-8")
            data += pack_bytes(self["reserved6"], 1)
        return data


class TSTypeInfoBlock(InfoDict):
    """ Specs from tsMuxer
    """

    def __init__(self):
        super().__init__()

    @classmethod
    def from_bytes(cls, data, **kwargs):
        self = cls()
        self["Length"] = unpack_bytes(data, 0, 2)
        self["ValidityFlags"] = unpack_bytes(data, 2, 1)
        self["FormatIdentifier"] = data[3:7].decode("utf-8")
        self["NetworkInformation"] = data[7:16]
        self["StreamFormatName"] = data[16:32]
        return self

    def calculate_display_size(self):
        return 32 - 2

    def to_bytes(self):
        self.check_constraints()
        data = b""
        data += pack_bytes(self["Length"], 2)
        data += pack_bytes(self["ValidityFlags"], 1)
        data += self["FormatIdentifier"].encode("utf-8")
        data += self["NetworkInformation"]
        data += self["StreamFormatName"]

        return data


class SequenceInfo(InfoDict):
    def __init__(self):
        super().__init__()

    @classmethod
    def from_bytes(cls, data, **kwargs):

        self = cls()
        self["Length"] = unpack_bytes(data, 0, 4)
        self["reserved1"] = unpack_bytes(data, 4, 1)
        self["NumberOfATCSequences"] = unpack_bytes(data, 5, 1)
        read_index = 6
        self["ATCSequences"] = []
        for i in range(self["NumberOfATCSequences"]):
            num_stc_seq = unpack_bytes(data, read_index + 4, 1)
            act_real_length = 6 + num_stc_seq * 14
            self["ATCSequences"].append(ATCSequence.from_bytes(data[read_index:read_index + act_real_length]))
            read_index += act_real_length

        return self

    def calculate_display_size(self):
        real_length = 6
        for i in self["ATCSequences"]:
            real_length += i.calculate_display_size()
        return real_length - 4

    def update_counts(self):
        self["NumberOfATCSequences"] = len(self["ATCSequences"])

    def check_constraints(self):
        super().check_constraints()
        assert self["NumberOfATCSequences"] == len(self["ATCSequences"])

    def to_bytes(self):
        self.check_constraints()
        data = b""
        data += pack_bytes(self["Length"], 4)
        data += pack_bytes(self["reserved1"], 1)
        data += pack_bytes(self["NumberOfATCSequences"], 1)
        for i in self["ATCSequences"]:
            data += i.to_bytes()
        return data


class ATCSequence(InfoDict):
    def __init__(self):
        super().__init__()

    @classmethod
    def from_bytes(cls, data, **kwargs):

        self = cls()
        self["SPNATCStart"] = unpack_bytes(data, 0, 4)
        self["NumberOfSTCSequences"] = unpack_bytes(data, 4, 1)
        self["OffsetSTCID"] = unpack_bytes(data, 5, 1)
        self["STCSequences"] = []
        for i in range(self["NumberOfSTCSequences"]):
            self["STCSequences"].append(STCSequence.from_bytes(data[6 + 14 * i:6 + 14 * (i + 1)]))

        return self

    def calculate_display_size(self):
        return 6 + 14 * len(self["STCSequences"])

    def update_counts(self):
        self["NumberOfSTCSequences"] = len(self["STCSequences"])

    def check_constraints(self):
        super().check_constraints()
        assert self["NumberOfSTCSequences"] == len(self["STCSequences"])

    def to_bytes(self):
        self.check_constraints()
        data = b""
        data += pack_bytes(self["SPNATCStart"], 4)
        data += pack_bytes(self["NumberOfSTCSequences"], 1)
        data += pack_bytes(self["OffsetSTCID"], 1)
        for i in self["STCSequences"]:
            data += i.to_bytes()
        return data


class STCSequence(InfoDict):
    def __init__(self):
        super().__init__()

    @classmethod
    def from_bytes(cls, data, **kwargs):
        self = cls()
        self["PCRPID"] = unpack_bytes(data, 0, 2)
        self["SPNSTCStart"] = unpack_bytes(data, 2, 4)
        self["PresentationStartTime"] = unpack_bytes(data, 6, 4)
        self["PresentationEndTime"] = unpack_bytes(data, 10, 4)

        return self

    def to_bytes(self):
        self.check_constraints()
        data = b""
        data += pack_bytes(self["PCRPID"], 2)
        data += pack_bytes(self["SPNSTCStart"], 4)
        data += pack_bytes(self["PresentationStartTime"], 4)
        data += pack_bytes(self["PresentationEndTime"], 4)
        return data


class ProgramInfo(InfoDict):
    def __init__(self):
        super().__init__()

    @classmethod
    def from_bytes(cls, data, **kwargs):

        self = cls()
        self["Length"] = unpack_bytes(data, 0, 4)
        self["reserved1"] = unpack_bytes(data, 4, 1)
        self["NumberOfPrograms"] = unpack_bytes(data, 5, 1)
        read_index = 6
        self["Programs"] = []
        for i in range(self["NumberOfPrograms"]):
            num_stream_ps = unpack_bytes(data, read_index + 6, 1)
            program_offset = 8
            for j in range(num_stream_ps):
                program_offset += 2
                program_offset += unpack_bytes(data, read_index + program_offset, 1) + 1
            self["Programs"].append(Program.from_bytes(data[read_index:read_index + program_offset]))
            read_index += program_offset

        return self

    def calculate_display_size(self):
        real_length = 6
        for i in self["Programs"]:
            real_length += i.calculate_display_size()
        return real_length - 4

    def update_counts(self):
        self["NumberOfPrograms"] = len(self["Programs"])

    def check_constraints(self):
        super().check_constraints()
        assert self["NumberOfPrograms"] == len(self["Programs"])

    def to_bytes(self):
        self.check_constraints()
        data = b""
        data += pack_bytes(self["Length"], 4)
        data += pack_bytes(self["reserved1"], 1)
        data += pack_bytes(self["NumberOfPrograms"], 1)
        for i in self["Programs"]:
            data += i.to_bytes()
        return data


class Program(InfoDict):
    def __init__(self):
        super().__init__()

    @classmethod
    def from_bytes(cls, data, **kwargs):

        self = cls()
        self["SPNProgramSequenceStart"] = unpack_bytes(data, 0, 4)
        self["ProgramMapPID"] = unpack_bytes(data, 4, 2)
        self["NumberOfStreamsInPS"] = unpack_bytes(data, 6, 1)
        self["NumberOfGroups"] = unpack_bytes(data, 7, 1)
        read_index = 8
        self["StreamsInPS"] = []
        for i in range(self["NumberOfStreamsInPS"]):
            streams_in_ps = InfoDict()
            streams_in_ps["StreamPID"] = unpack_bytes(data, read_index, 2)
            read_index += 2
            scinfo_display_size = unpack_bytes(data, read_index, 1)
            streams_in_ps["StreamCodingInfo"] = StreamCodingInfo.from_bytes(
                data[read_index:read_index + scinfo_display_size + 1])
            self["StreamsInPS"].append(streams_in_ps)
            read_index += scinfo_display_size + 1

        return self

    def calculate_display_size(self):
        real_length = 8
        for i in self["StreamsInPS"]:
            real_length += 2
            real_length += i["StreamCodingInfo"].calculate_display_size() + 1
        return real_length

    def update_counts(self):
        self["NumberOfStreamsInPS"] = len(self["StreamsInPS"])

    def check_constraints(self):
        super().check_constraints()
        assert self["NumberOfStreamsInPS"] == len(self["StreamsInPS"])

    def to_bytes(self):
        self.check_constraints()
        data = b""
        data += pack_bytes(self["SPNProgramSequenceStart"], 4)
        data += pack_bytes(self["ProgramMapPID"], 2)
        data += pack_bytes(self["NumberOfStreamsInPS"], 1)
        data += pack_bytes(self["NumberOfGroups"], 1)
        for i in self["StreamsInPS"]:
            data += pack_bytes(i["StreamPID"], 2)
            data += i["StreamCodingInfo"].to_bytes()
        return data


class StreamCodingInfo(InfoDict):
    def __init__(self):
        super().__init__()

    @classmethod
    def from_bytes(cls, data, **kwargs):

        self = cls()
        self["Length"] = unpack_bytes(data, 0, 1)
        self["StreamCodingType"] = unpack_bytes(data, 1, 1)
        if self["StreamCodingType"] in [0x01, 0x02, 0x1B, 0xEA]:
            self["VideoFormat"], self["FrameRate"] = divmod(unpack_bytes(data, 2, 1), 2 ** 4)
            flags = unpack_bytes(data, 3, 1)
            self["VideoAspect"], flags = divmod(flags, 2 ** 4)
            self["reserved1"], flags = divmod(flags, 2 ** 2)
            self["OCFlag"], self["reserved2"] = divmod(flags, 2)
            self["reserved3"] = unpack_bytes(data, 4, 2)
            self["padding"] = data[6:]
        elif self["StreamCodingType"] in [0x24]:
            self["VideoFormat"], self["FrameRate"] = divmod(unpack_bytes(data, 2, 1), 2 ** 4)
            flags = unpack_bytes(data, 3, 1)
            self["VideoAspect"], flags = divmod(flags, 2 ** 4)
            self["reserved4"], flags = divmod(flags, 2 ** 2)
            self["OCFlag"], self["CRFlag"] = divmod(flags, 2)
            self["DynamicRangeType"], self["ColorSpace"] = divmod(unpack_bytes(data, 4, 1), 2 ** 4)
            self["HDRPlusFlag"], self["reserved5"] = divmod(unpack_bytes(data, 5, 1), 2 ** 7)
            self["padding"] = data[6:]
        elif self["StreamCodingType"] in [0x03, 0x04, 0x80, 0x81, 0x82, 0x83, 0x84, 0x85, 0x86, 0xA1, 0xA2]:
            self["AudioFormat"], self["SampleRate"] = divmod(unpack_bytes(data, 2, 1), 2 ** 4)
            self["Language"] = data[3:6].decode("utf-8")
            self["padding"] = data[6:]
        elif self["StreamCodingType"] in [0x90, 0x91]:
            self["Language"] = data[2:5].decode("utf-8")
            self["padding"] = data[5:]
        elif self["StreamCodingType"] in [0x92]:
            self["CharCode"] = unpack_bytes(data, 2, 1)
            self["Language"] = data[3:6].decode("utf-8")
            self["padding"] = data[6:]

        return self

    def calculate_display_size(self):
        return self["Length"]

    def to_bytes(self):
        self.check_constraints()
        data = b""
        data += pack_bytes(self["Length"], 1)
        data += pack_bytes(self["StreamCodingType"], 1)

        if self["StreamCodingType"] in [0x01, 0x02, 0x1B, 0xEA]:
            data += pack_bytes((self["VideoFormat"] << 4) + self["FrameRate"], 1)
            data += pack_bytes(
                (self["VideoAspect"] << 4) + (self["reserved1"] << 2) + (self["OCFlag"] << 1) + self["reserved2"], 1)
            data += pack_bytes(self["reserved3"], 2)
            data += self["padding"]
        elif self["StreamCodingType"] in [0x24]:
            data += pack_bytes((self["VideoFormat"] << 4) + self["FrameRate"], 1)
            data += pack_bytes(
                (self["VideoAspect"] << 4) + (self["reserved4"] << 2) + (self["OCFlag"] << 1) + self["CRFlag"], 1)
            data += pack_bytes((self["DynamicRangeType"] << 4) + self["ColorSpace"], 1)
            data += pack_bytes((self["HDRPlusFlag"] << 7) + self["reserved5"], 1)
            data += self["padding"]
        elif self["StreamCodingType"] in [0x03, 0x04, 0x80, 0x81, 0x82, 0x83, 0x84, 0x85, 0x86, 0xA1, 0xA2]:
            data += pack_bytes((self["AudioFormat"] << 4) + self["SampleRate"], 1)
            data += self["Language"].encode("utf-8")
            data += self["padding"]
        elif self["StreamCodingType"] in [0x90, 0x91]:
            data += self["Language"].encode("utf-8")
            data += self["padding"]
        elif self["StreamCodingType"] in [0x92]:
            data += pack_bytes(self["CharCode"], 1)
            data += self["Language"].encode("utf-8")
            data += self["padding"]

        assert len(data) == self["Length"] + 1
        return data


class CPI(InfoDict):
    def __init__(self):
        super().__init__()

    @classmethod
    def from_bytes(cls, data, **kwargs):
        self = cls()
        self["Length"] = unpack_bytes(data, 0, 4)
        if self["Length"]:
            flags = unpack_bytes(data, 4, 2)
            self["reserved1"], self["CPIType"] = divmod(flags, 2 ** 4)
            # EPMap starts here, at relative real position 6, display position 2
            self["reserved2"] = unpack_bytes(data, 6, 1)
            self["NumberOfStreamPIDEntries"] = unpack_bytes(data, 7, 1)
            # Do not create a new class for StreamPIDEntries, since its data is not continuous, conversation should
            # be handled here instead of calling subclass methods
            self["StreamPIDEntries"] = []
            # meta-info block contains 12 Bytes
            for i in range(self["NumberOfStreamPIDEntries"]):
                spid_entry = InfoDict()
                # read_offset is static
                read_offset = 8 + 12 * i
                tmp = unpack_bytes(data, read_offset, 8)
                spid_entry["StreamPID"], tmp = divmod(tmp, 2 ** 48)
                spid_entry["reserved3"], tmp = divmod(tmp, 2 ** 38)
                spid_entry["EPStreamType"], tmp = divmod(tmp, 2 ** 34)
                spid_entry["NumberOfEPCoarseEntries"], spid_entry["NumberOfEPFineEntries"] = divmod(tmp, 2 ** 18)
                spid_entry["EPMapForOneStreamPIDStartAddress"] = unpack_bytes(data, read_offset + 8, 4)
                self["StreamPIDEntries"].append(spid_entry)

            # block_start_address is dynamic
            current_address = 8 + 12 * self["NumberOfStreamPIDEntries"]
            for spid_entry in self["StreamPIDEntries"]:
                # Each block is of size 4 + 8 * NumberOfEPCoarseEntries + 4 * NumberOfEPFineEntries
                # address formula 1
                assert spid_entry["EPMapForOneStreamPIDStartAddress"] == current_address - 6
                spid_entry["EPFineTableStartAddress"] = unpack_bytes(data, current_address, 4)
                current_address += 4
                spid_entry["EPCoarseEntries"] = []
                for j in range(spid_entry["NumberOfEPCoarseEntries"]):
                    spid_entry["EPCoarseEntries"].append(EPCoarseEntry.from_bytes(
                        data[current_address:current_address + 8]
                    ))
                    current_address += 8

                # address formula 2
                assert spid_entry["EPFineTableStartAddress"] + \
                       spid_entry["EPMapForOneStreamPIDStartAddress"] == current_address - 6
                spid_entry["EPFineEntries"] = []
                for j in range(spid_entry["NumberOfEPFineEntries"]):
                    spid_entry["EPFineEntries"].append(EPFineEntry.from_bytes(
                        data[current_address:current_address + 4]
                    ))
                    current_address += 4

        return self

    def calculate_display_size(self):
        if self["Length"]:
            real_length = 8 + 12 * len(self["StreamPIDEntries"])
            for spid_entry in self["StreamPIDEntries"]:
                real_length += 4 + 8 * len(spid_entry["EPCoarseEntries"]) + 4 * len(spid_entry["EPFineEntries"])
            return real_length - 4
        else:
            return 0

    def update_counts(self):
        self["NumberOfStreamPIDEntries"] = len(self["StreamPIDEntries"])
        for spid_entry in self["StreamPIDEntries"]:
            spid_entry["NumberOfEPCoarseEntries"] = len(spid_entry["EPCoarseEntries"])
            spid_entry["NumberOfEPFineEntries"] = len(spid_entry["EPFineEntries"])
        current_address = 8 + 12 * len(self["StreamPIDEntries"])
        for spid_entry in self["StreamPIDEntries"]:
            spid_entry["EPMapForOneStreamPIDStartAddress"] = current_address - 6
            current_address += 4 + 8 * len(spid_entry["EPCoarseEntries"])
            spid_entry["EPFineTableStartAddress"] = current_address - 6 - spid_entry["EPMapForOneStreamPIDStartAddress"]
            current_address += 4 * len(spid_entry["EPFineEntries"])

    def check_constraints(self):
        super().check_constraints()
        assert self["NumberOfStreamPIDEntries"] == len(self["StreamPIDEntries"])
        for spid_entry in self["StreamPIDEntries"]:
            assert spid_entry["NumberOfEPCoarseEntries"] == len(spid_entry["EPCoarseEntries"])
            assert spid_entry["NumberOfEPFineEntries"] == len(spid_entry["EPFineEntries"])
        current_address = 8 + 12 * len(self["StreamPIDEntries"])
        for spid_entry in self["StreamPIDEntries"]:
            assert spid_entry["EPMapForOneStreamPIDStartAddress"] == current_address - 6
            current_address += 4 + 8 * len(spid_entry["EPCoarseEntries"])
            assert spid_entry["EPFineTableStartAddress"] == current_address - 6 - spid_entry[
                "EPMapForOneStreamPIDStartAddress"]
            current_address += 4 * len(spid_entry["EPFineEntries"])

    def to_bytes(self):
        self.check_constraints()
        data = b""
        data += pack_bytes(self["Length"], 4)
        if self["Length"]:
            data += pack_bytes((self["reserved1"] << 4) + self["CPIType"], 2)
            data += pack_bytes(self["reserved2"], 1)
            data += pack_bytes(self["NumberOfStreamPIDEntries"], 1)
            for spid_entry in self["StreamPIDEntries"]:
                data += pack_bytes((spid_entry["StreamPID"] << 48)
                                   + (spid_entry["reserved3"] << 38)
                                   + (spid_entry["EPStreamType"] << 34)
                                   + (spid_entry["NumberOfEPCoarseEntries"] << 18)
                                   + spid_entry["NumberOfEPFineEntries"], 8)
                data += pack_bytes(spid_entry["EPMapForOneStreamPIDStartAddress"], 4)
            for spid_entry in self["StreamPIDEntries"]:
                data += pack_bytes(spid_entry["EPFineTableStartAddress"], 4)
                for i in spid_entry["EPCoarseEntries"]:
                    data += i.to_bytes()
                for i in spid_entry["EPFineEntries"]:
                    data += i.to_bytes()
        return data


class EPCoarseEntry(InfoDict):
    def __init__(self):
        super().__init__()

    @classmethod
    def from_bytes(cls, data, **kwargs):
        self = cls()
        flags = unpack_bytes(data, 0, 4)
        self["RefToEPFineID"], self["PTSEPCoarse"] = divmod(flags, 2 ** 14)
        self["SPNEPCoarse"] = unpack_bytes(data, 4, 4)
        return self

    def to_bytes(self):
        self.check_constraints()
        data = b""
        data += pack_bytes((self["RefToEPFineID"] << 14) + self["PTSEPCoarse"], 4)
        data += pack_bytes(self["SPNEPCoarse"], 4)
        return data


class EPFineEntry(InfoDict):
    def __init__(self):
        super().__init__()

    @classmethod
    def from_bytes(cls, data, **kwargs):
        self = cls()
        flags = unpack_bytes(data, 0, 4)
        self["IsAngleChangePoint"], flags = divmod(flags, 2 ** 31)
        self["IEndPositionOffset"], flags = divmod(flags, 2 ** 28)
        self["PTSEPFine"], self["SPNEPFine"] = divmod(flags, 2 ** 17)
        return self

    def to_bytes(self):
        self.check_constraints()
        data = b""
        data += pack_bytes(
            (self["IsAngleChangePoint"] << 31) + (self["IEndPositionOffset"] << 28) + (self["PTSEPFine"] << 17) +
            self["SPNEPFine"], 4)
        return data


class ClipMark(InfoDict):
    """ No specs available
    """

    def __init__(self):
        super().__init__()

    @classmethod
    def from_bytes(cls, data, **kwargs):
        self = cls()
        self["Length"] = unpack_bytes(data, 0, 4)
        if self["Length"] != 0:
            self["Data"] = data[4:]
        return self

    def calculate_display_size(self):
        if self["Length"] != 0:
            return len(self["data"])
        else:
            return 0

    def to_bytes(self):
        self.check_constraints()
        data = b""
        data += pack_bytes(self["Length"], 4)
        if self["Length"] != 0:
            data += self["Data"]

        return data


class ClipInformationFile:
    def __init__(self, filename=None):
        if not filename:
            self.data = CLPIHeader()
        else:
            self.load(filename)

    def load(self, filename):
        with open(filename, "rb") as f:
            data = f.read()
        self.data = CLPIHeader.from_bytes(data)

    def save(self, destination, overwrite=False):
        self.data.update_constants()
        self.data.update_addresses()
        if os.path.exists(destination) and not overwrite:
            raise FileExistsError()
        os.makedirs(os.path.dirname(destination), exist_ok=True)
        with open(destination, "wb") as f:
            f.write(self.data.to_bytes())
