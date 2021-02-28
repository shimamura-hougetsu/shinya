import argparse

from shinya.bd.mpls import MoviePlaylist, PlayListMarkItem


def process_uomask(d):
    keys_to_modify = ["ChapterSearch", "TimeSearch", "SkipToNextPoint", "SkipToPrevPoint", "ForwardPlay",
                      "BackwardPlay"]
    for key in keys_to_modify:
        d[key] = 0


def main(source, destination):
    mpls = MoviePlaylist(source)
    process_uomask(mpls.data["AppInfoPlayList"]["UOMaskTable"])
    for play_item in mpls.data["PlayList"]["PlayItems"]:
        process_uomask(play_item["UOMaskTable"])
    # add playlist mark
    mark_time = mpls.data["PlayList"]["PlayItems"][-1]["OUTTime"]
    ref_pi = len(mpls.data["PlayList"]["PlayItems"]) - 1
    plm = PlayListMarkItem([('reserved1', 0),
                            ('MarkType', 1),
                            ('RefToPlayItemID', ref_pi),
                            ('MarkTimeStamp', mark_time),
                            ('EntryESPID', 65535),
                            ('Duration', 0)]
                           )
    mpls.data["PlayListMark"]["PlayListMarks"].append(plm)
    mpls.save(destination)


if __name__ == '__main__':
    parser = argparse.ArgumentParser('enable skipping, forwarding, etc in ads/warnings')
    parser.add_argument("source", type=str, help="source mpls file")
    parser.add_argument("destination", type=str, help="mpls save destination")
    args = parser.parse_args()
    main(args.source, args.destination)
