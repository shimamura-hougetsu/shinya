import argparse
import os

from shinya.tools.chapter import Chapter


def main(source, destination, single_file):
    chapters = Chapter.from_mpls(source)
    filename, _ = os.path.splitext(os.path.basename(source))
    if single_file:
        chapters = sum(i[1] for i in chapters)
        chapters.export(os.path.join(destination, f"{filename}.xml"))
    else:
        for clip_name, chapter in chapters:
            chapter.export(os.path.join(destination, f"{filename}_{clip_name}.xml"))


if __name__ == '__main__':
    parser = argparse.ArgumentParser("Reads mpls and export chapters to xml files for mkv")
    parser.add_argument("source", type=str, help="source mpls file")
    parser.add_argument("destination", type=str, help="folder to save xml files")
    parser.add_argument("-s", "--single", action="store_true", default=False,
                        help="whether to join all play items into one chapter file")
    args = parser.parse_args()
    main(args.source, args.destination, args.single)
