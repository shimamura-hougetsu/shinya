import argparse

from shiny.mpls import MoviePlaylist


def main(source, destination):
    mpls = MoviePlaylist(source)
    mpls.save(destination)


if __name__ == '__main__':
    parser = argparse.ArgumentParser("reads and generates the same mpls file, for testing only")
    parser.add_argument("source", type=str, help="source mpls file")
    parser.add_argument("destination", type=str, help="mpls save destination")
    args = parser.parse_args()
    main(args.source, args.destination)
