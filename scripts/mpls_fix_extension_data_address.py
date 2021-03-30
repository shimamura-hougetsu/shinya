import argparse

from shinya.bd.mpls import MoviePlaylist
from shinya.common.io import unpack_bytes, pack_bytes


def check_integrity(input_file):
    success = True
    try:
        MoviePlaylist(input_file)
    except:
        success = False
    return success


def fix_ext_address(source, destination):
    with open(source, "rb") as f:
        data = f.read()
    plm_addr = unpack_bytes(data, 12, 4)
    ext_addr = unpack_bytes(data, 16, 4)
    plm_size = unpack_bytes(data, plm_addr, 4)
    if ext_addr:
        expected_ext_addr = plm_addr + plm_size + 4
        if expected_ext_addr != ext_addr:
            data = data[:16] + pack_bytes(expected_ext_addr, 4) + data[20:]
    with open(destination, "wb") as f:
        f.write(data)


def main(source, destination):
    if check_integrity(source):
        print("[OK] The playlist does not seem to contain errors.")
    else:
        fix_ext_address(source, destination)
        if check_integrity(destination):
            print("[OK] The extension address has been fixed.")
        else:
            print("[FAILED] The playlist seems to have other errors.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser("fix wrong extension data start address in mpls files")
    parser.add_argument("source", type=str, help="source mpls file")
    parser.add_argument("destination", type=str, help="mpls save destination")
    args = parser.parse_args()
    main(args.source, args.destination)
