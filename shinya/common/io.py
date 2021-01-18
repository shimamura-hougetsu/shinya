import struct

FORMAT_CHAR = {1: ">B", 2: ">H", 4: ">I", 8: ">Q"}


def unpack_bytes(data, offset, length):
    result, = struct.unpack(FORMAT_CHAR[length], data[offset:offset + length])
    return result


def pack_bytes(data, length):
    return struct.pack(FORMAT_CHAR[length], data)

