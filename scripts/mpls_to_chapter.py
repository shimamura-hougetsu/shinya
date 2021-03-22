import argparse
import os

from shinya.tools.chapter import Chapter


def main(source, destination, single_file, qpfile):
    chapters = Chapter.from_mpls(source)
    filename, _ = os.path.splitext(os.path.basename(source))
    if single_file:
        chapters = sum(i[1] for i in chapters)
        chapters.export(os.path.join(destination, f"{filename}.xml"))
    else:
        for clip_name, chapter, attr in chapters:
            chapter.export(os.path.join(destination, f"{filename}_{clip_name}.xml"))
            if qpfile:
                chapter.export(os.path.join(destination, f"{filename}_{clip_name}.qpf"), export_format="qpf",
                               clip_attr=attr)


if __name__ == '__main__':
    parser = argparse.ArgumentParser("Reads mpls and export chapters to xml mkv chapter files and qp files")
    parser.add_argument("source", type=str, help="source mpls file")
    parser.add_argument("destination", type=str, help="folder to save xml files")
    parser.add_argument("-s", "--single", action="store_true", default=False,
                        help="whether to join all play items into one chapter file")
    parser.add_argument("-q", "--qpfile", action="store_true", default=False,
                        help="export a qpfile along with the chapter file")

    args = parser.parse_args()
    if args.single and args.qpfile:
        print('You should not create a single qpfile for multiple clips.')
        exit(-1)
    main(args.source, args.destination, args.single, args.qpfile)
