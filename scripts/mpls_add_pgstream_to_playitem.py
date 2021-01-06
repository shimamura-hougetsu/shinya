import argparse

from shiny.info_dict import InfoDict
from shiny.mpls import MoviePlaylist
from shiny.mpls import StreamEntry, StreamAttributes


def main(source, destination, clip_filenames, language):
    assert len(language) == 3

    mpls = MoviePlaylist(source)
    for clip_filename in clip_filenames:
        assert len(clip_filename) == 5
        target_index_list = []
        for index, play_item in enumerate(mpls.dict['PlayList']['PlayItems']):
            if play_item['ClipInformationFileName'] == clip_filename:
                target_index_list.append(index)
        if len(target_index_list) == 0:
            print(f'Target m2ts file {clip_filename} is not found in the playlist.')
            exit(-1)
        elif len(target_index_list) > 1:
            print(f'More than one instance of {clip_filename} are found in the playlist.')
            exit(-1)
        target_index = target_index_list[0]
        subtitle_list = mpls.dict['PlayList']['PlayItems'][target_index]['STNTable']['PrimaryPGStreamEntries']

        se = StreamEntry()
        se['Length'] = 9
        se['StreamType'] = 1
        if len(subtitle_list) == 0:
            se['RefToStreamPID'] = 1200
        else:
            se['RefToStreamPID'] = subtitle_list[-1]['StreamEntry']['RefToStreamPID'] + 1

        sa = StreamAttributes()
        sa['Length'] = 5
        sa['StreamCodingType'] = 0x90
        sa['LanguageCode'] = language
        stream_item = InfoDict()
        stream_item['StreamEntry'] = se
        stream_item['StreamAttributes'] = sa
        subtitle_list.append(stream_item)
        mpls.dict.update_constants()
    mpls.save(destination)


if __name__ == '__main__':
    parser = argparse.ArgumentParser("adds one or more subtitle streams to an existing playitem's stn table")
    parser.add_argument("source", type=str, help="source mpls file")
    parser.add_argument("destination", type=str, help="mpls save destination")
    parser.add_argument("clipfilenames", type=str, nargs='+', help="names of the m2ts file, five digits")
    parser.add_argument("-l", "--language", type=str, default="zho", help="language of subtitle, three characters")
    args = parser.parse_args()
    main(args.source, args.destination, args.clipfilenames, args.language)
