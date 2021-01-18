import argparse

from shinya.bd.mpls import MoviePlaylist


def process_uomask(d):
    for key in d.keys():
        d[key] = 0


def main(source, destination):
    mpls = MoviePlaylist(source)
    process_uomask(mpls.data["AppInfoPlayList"]["UOMaskTable"])
    for play_item in mpls.data["PlayList"]["PlayItems"]:
        process_uomask(play_item["UOMaskTable"])
    mpls.save(destination)


if __name__ == '__main__':
    parser = argparse.ArgumentParser('clear uomask table for all items')
    parser.add_argument("source", type=str, help="source mpls file")
    parser.add_argument("destination", type=str, help="mpls save destination")
    args = parser.parse_args()
    main(args.source, args.destination)
