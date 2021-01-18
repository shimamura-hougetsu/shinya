import os
from enum import IntEnum

from shinya.bd.extension_data import ExtensionData
from shinya.common.info_dict import InfoDict
from shinya.common.io import unpack_bytes, pack_bytes


class MOBJHeader(InfoDict):
    def __init__(self):
        super().__init__()

    @classmethod
    def from_bytes(cls, data, **kwargs):
        self = cls()
        self["TypeIndicator"] = data[0:4].decode("utf-8")
        self["VersionNumber"] = data[4:8].decode("utf-8")
        self["ExtensionDataStartAddress"] = unpack_bytes(data, 8, 4)
        self["reserved1"] = data[12:40]

        movie_object_length = unpack_bytes(data, 40, 4)
        self['MovieObjects'] = MovieObjects.from_bytes(data[40: 40 + movie_object_length + 4])

        if self["ExtensionDataStartAddress"]:
            assert (self["PlayListMarkStartAddress"] + movie_object_length + 4 == self[
                "ExtensionDataStartAddress"])
            extension_display_size = unpack_bytes(data, self["ExtensionDataStartAddress"], 4)
            assert self["ExtensionDataStartAddress"] + extension_display_size + 4 == len(data)
            self["ExtensionData"] = ExtensionData.from_bytes(
                data[self["ExtensionDataStartAddress"]: self["ExtensionDataStartAddress"] + extension_display_size + 4],
                self["ExtensionDataStartAddress"])
        else:
            assert 40 + movie_object_length + 4 == len(data)

        assert data == self.to_bytes()
        return self

    def update_addresses(self, offset=0):
        if self["ExtensionDataStartAddress"]:
            self["ExtensionDataStartAddress"] = 40 + self['MovieObjects']['Length'] + 4

    def check_constraints(self):
        if self["ExtensionDataStartAddress"]:
            movie_object_length = self["MovieObjects"].calculate_display_size()
            assert (self["PlayListMarkStartAddress"] + movie_object_length + 4 == self["ExtensionDataStartAddress"])

    def to_bytes(self):
        self.check_constraints()
        data = b""
        data += self["TypeIndicator"].encode("utf-8")
        data += self["VersionNumber"].encode("utf-8")
        data += pack_bytes(self["ExtensionDataStartAddress"], 4)
        data += self["reserved1"]

        data += self["MovieObjects"].to_bytes()
        if self["ExtensionDataStartAddress"]:
            data += self["ExtensionData"].to_bytes(self["ExtensionDataStartAddress"])
        return data


class MovieObjects(InfoDict):
    def __init__(self):
        super().__init__()

    @classmethod
    def from_bytes(cls, data, **kwargs):
        self = cls()
        self["Length"] = unpack_bytes(data, 0, 4)
        self["reserved1"] = unpack_bytes(data, 4, 4)
        self["NumberOfMobjs"] = unpack_bytes(data, 8, 2)

        self["Mobjs"] = []
        read_index = 10
        for i in range(self["NumberOfMobjs"]):
            n_navi_cmds = unpack_bytes(data, read_index + 2, 2)
            mobj_length = 4 + n_navi_cmds * 12
            self["Mobjs"].append(Mobj.from_bytes(data[read_index:read_index + mobj_length]))
            read_index += mobj_length
        return self

    def calculate_display_size(self):
        real_length = 10
        for i in self["Mobjs"]:
            real_length += i.calculate_display_size()
        return real_length - 4

    def update_counts(self):
        self["NumberOfMobjs"] = len(self["Mobjs"])

    def check_constraints(self):
        super().check_constraints()
        assert self["NumberOfMobjs"] == len(self["Mobjs"])

    def to_bytes(self, **kwargs):
        self.check_constraints()
        data = b""
        data += pack_bytes(self["Length"], 4)
        data += pack_bytes(self["reserved1"], 4)
        data += pack_bytes(self["NumberOfMobjs"], 2)
        for i in self["Mobjs"]:
            data += i.to_bytes()

        return data


class Mobj(InfoDict):
    def __init__(self):
        super().__init__()

    @classmethod
    def from_bytes(cls, data, **kwargs):
        self = cls()
        flags = unpack_bytes(data, 0, 2)
        self["ResumeIntentionFlag"] = flags >> 15 & 1
        self["MenuCallMask"] = flags >> 14 & 1
        self["TitleSearchMask"] = flags >> 13 & 1
        self["reserved1"] = flags % 2 ** 13
        self["NumberOfNavigationCommands"] = unpack_bytes(data, 2, 2)

        self["NavigationCommands"] = []
        for i in range(self["NumberOfNavigationCommands"]):
            self["NavigationCommands"].append(NavigationCommand.from_bytes(data[4 + i * 12:4 + (i + 1) * 12]))
        return self

    def calculate_display_size(self):
        return 4 + 12 * len(self["NavigationCommands"])

    def update_counts(self):
        self["NumberOfNavigationCommands"] = len(self["NavigationCommands"])

    def check_constraints(self):
        super().check_constraints()
        assert self["NumberOfNavigationCommands"] == len(self["NavigationCommands"])

    def to_bytes(self, **kwargs):
        self.check_constraints()
        data = b""
        data += pack_bytes(
            self["ResumeIntentionFlag"] * 2 ** 15 + self["MenuCallMask"] * 2 ** 14 + self["TitleSearchMask"] * 2 ** 13 +
            self["reserved1"], 2)
        data += pack_bytes(self["NumberOfNavigationCommands"], 2)
        for i in self["NavigationCommands"]:
            data += i.to_bytes()

        return data


class CommandGroup(IntEnum):
    BRANCH = 0
    CMP = 1
    SET = 2


class BranchCommandSubGroup(IntEnum):
    GOTO = 0
    JUMP = 1
    PLAY = 2


class SetCommandSubGroup(IntEnum):
    SET = 0
    SETSYSTEM = 1


class NavigationCommand(InfoDict):
    def __init__(self):
        super().__init__()

    @classmethod
    def from_bytes(cls, data, **kwargs):
        assert len(data) == 12
        self = cls()
        flags = unpack_bytes(data, 0, 1)
        self["OperandCount"], flags = divmod(flags, 2 ** 5)
        self["CommandGroup"], self["CommandSubGroup"] = divmod(flags, 2 ** 3)
        flags = unpack_bytes(data, 1, 1)
        self["DestinationImmediateValueFlag"] = flags >> 7 & 1
        self["SourceImmediateValueFlag"] = flags >> 6 & 1
        self["reserved1"], self["BranchOption"] = divmod(flags % 2 ** 6, 2 ** 4)
        flags = unpack_bytes(data, 2, 1)
        self["reserved2"], self["CompareOption"] = divmod(flags, 2 ** 4)
        flags = unpack_bytes(data, 3, 1)
        self["reserved3"], self["SetOption"] = divmod(flags, 2 ** 5)
        self["Destination"] = unpack_bytes(data, 4, 4)
        self["Source"] = unpack_bytes(data, 8, 4)
        return self

    def to_bytes(self, **kwargs):
        data = b""
        data += pack_bytes((self["OperandCount"] << 5) + (self["CommandGroup"] << 3) + self["CommandSubGroup"], 1)
        data += pack_bytes((self["DestinationImmediateValueFlag"] << 7) + (self["SourceImmediateValueFlag"] << 6)
                           + (self["reserved1"] << 4) + self["BranchOption"], 1)
        data += pack_bytes((self["reserved2"] << 4) + self["CompareOption"], 1)
        data += pack_bytes((self["reserved3"] << 5) + self["SetOption"], 1)
        data += pack_bytes(self["Destination"], 4)
        data += pack_bytes(self["Source"], 4)
        return data

    def get_command(self):
        if self["CommandGroup"] == CommandGroup.BRANCH:
            if self["CommandSubGroup"] == BranchCommandSubGroup.GOTO:
                if self["BranchOption"] == 0b000:
                    return "Branch_Nop"
                elif self["BranchOption"] == 0b001:
                    return "Branch_GoTo"
                elif self["BranchOption"] == 0b010:
                    return "Branch_Break"
                else:
                    raise ValueError()
            elif self["CommandSubGroup"] == BranchCommandSubGroup.JUMP:
                if self["BranchOption"] == 0b000:
                    return "Branch_JumpObject"
                elif self["BranchOption"] == 0b001:
                    return "Branch_JumpTitle"
                elif self["BranchOption"] == 0b010:
                    return "Branch_CallObject"
                elif self["BranchOption"] == 0b011:
                    return "Branch_CallTitle"
                elif self["BranchOption"] == 0b100:
                    return "Branch_Resume"
                else:
                    raise ValueError()
            elif self["CommandSubGroup"] == BranchCommandSubGroup.PLAY:
                if self["BranchOption"] == 0b000:
                    return "Branch_PlayList"
                elif self["BranchOption"] == 0b001:
                    return "Branch_PlayItem"
                elif self["BranchOption"] == 0b010:
                    return "Branch_PlayMark"
                elif self["BranchOption"] == 0b011:
                    return "Branch_Terminate"
                elif self["BranchOption"] == 0b100:
                    return "Branch_LinkItem"
                elif self["BranchOption"] == 0b101:
                    return "Branch_LinkMark"
                else:
                    raise ValueError()
            else:
                raise ValueError()
        elif self["CommandGroup"] == CommandGroup.CMP:
            if self["CompareOption"] == 0b001:
                return "Compare_BC"
            elif self["CompareOption"] == 0b010:
                return "Compare_EQ"
            elif self["CompareOption"] == 0b011:
                return "Compare_NE"
            elif self["CompareOption"] == 0b100:
                return "Compare_GE"
            elif self["CompareOption"] == 0b101:
                return "Compare_GT"
            elif self["CompareOption"] == 0b110:
                return "Compare_LE"
            elif self["CompareOption"] == 0b111:
                return "Compare_LT"
            else:
                raise ValueError()
        elif self["CommandGroup"] == CommandGroup.SET:
            if self["CommandSubGroup"] == SetCommandSubGroup.SET:
                if self["SetOption"] == 0b00001:
                    return "Set_Move"
                elif self["SetOption"] == 0b00010:
                    return "Set_Swap"
                elif self["SetOption"] == 0b00011:
                    return "Set_Add"
                elif self["SetOption"] == 0b00100:
                    return "Set_Sub"
                elif self["SetOption"] == 0b00101:
                    return "Set_Mul"
                elif self["SetOption"] == 0b00110:
                    return "Set_Div"
                elif self["SetOption"] == 0b00111:
                    return "Set_Mod"
                elif self["SetOption"] == 0b01000:
                    return "Set_Rnd"
                elif self["SetOption"] == 0b01001:
                    return "Set_And"
                elif self["SetOption"] == 0b01010:
                    return "Set_Or"
                elif self["SetOption"] == 0b01011:
                    return "Set_Xor"
                elif self["SetOption"] == 0b01100:
                    return "Set_Bitset"
                elif self["SetOption"] == 0b01101:
                    return "Set_Bitclr"
                elif self["SetOption"] == 0b01110:
                    return "Set_ShiftLeft"
                elif self["SetOption"] == 0b01111:
                    return "Set_ShiftRight"
                else:
                    raise ValueError()
            elif self["CommandSubGroup"] == SetCommandSubGroup.SETSYSTEM:
                if self["SetOption"] == 0b00001:
                    return "Set_SetStream"
                elif self["SetOption"] == 0b00010:
                    return "Set_SetNVTimer"
                elif self["SetOption"] == 0b00011:
                    return "Set_ButtonPage"
                elif self["SetOption"] == 0b00100:
                    return "Set_EnableButton"
                elif self["SetOption"] == 0b00101:
                    return "Set_DisableButton"
                elif self["SetOption"] == 0b00110:
                    return "Set_SetSecondaryStream"
                elif self["SetOption"] == 0b00111:
                    return "Set_PopupOff"
                elif self["SetOption"] == 0b01000:
                    return "Set_StillOn"
                elif self["SetOption"] == 0b01001:
                    return "Set_StillOff"
                else:
                    raise ValueError()
            else:
                raise ValueError()
        else:
            raise ValueError()


class MovieObjectFile:
    def __init__(self, filename=None):
        if not filename:
            self.data = MOBJHeader()
        else:
            self.load(filename)

    def load(self, filename):
        with open(filename, "rb") as f:
            data = f.read()
        self.data = MOBJHeader.from_bytes(data)

    def save(self, destination, overwrite=False):
        self.data.update_constants()
        self.data.update_addresses()
        if os.path.exists(destination) and not overwrite:
            raise FileExistsError()
        os.makedirs(os.path.dirname(destination), exist_ok=True)
        with open(destination, "wb") as f:
            f.write(self.data.to_bytes())
