import argparse

from shinya.bd import MoviePlaylistFile


def main(source, destination):
    mpls = MoviePlaylistFile(source)
    for subpath in mpls.data['PlayList']['SubPaths']:
        if subpath['SubPathType'] == 5:
            for subplayitem in subpath['SubPlayItems']:
                playitem = mpls.data['PlayList']['PlayItems'][subplayitem['SyncPlayItemID']]
                assert subplayitem['SyncStartPTS'] == subplayitem['INTime']
                assert subplayitem['INTime'] == playitem['INTime']
                for pgs_info in playitem['STNTable']['PrimaryPGStreamEntries']:
                    if not destination:
                        assert pgs_info['StreamEntry']['RefToSubClipID'] == 0
                    else:
                        pgs_info['StreamEntry']['RefToSubClipID'] = 0
    if destination:
        mpls.save(destination)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        "checks some constraints on PD compatibility for plugin structures, modify if destination is given")
    parser.add_argument("source", type=str, help="source mpls file")
    parser.add_argument("-d", "--destination", type=str, help="mpls save destination")
    args = parser.parse_args()
    main(args.source, args.destination)
