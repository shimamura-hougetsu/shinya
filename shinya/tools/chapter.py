import os
from copy import deepcopy

from lxml import etree

from shinya.bd.mpls import MoviePlaylist


class MatroskaXMLChapter:
    """
    Minimal implementation of xml chapter generated from blu-ray discs
    """

    def __init__(self, chapters):
        assert isinstance(chapters, Chapter)
        self.chapters = chapters
        self.xml_chapter = etree.Element('Chapters')
        edition_entry = etree.SubElement(self.xml_chapter, 'EditionEntry')
        edition_flag_hidden = etree.SubElement(edition_entry, 'EditionFlagHidden')
        edition_flag_hidden.text = "0"
        edition_flag_default = etree.SubElement(edition_entry, 'EditionFlagDefault')
        edition_flag_default.text = "1"
        for index, chapter_entry in enumerate(self.chapters):
            chapter_atom = etree.SubElement(edition_entry, "ChapterAtom")
            chapter_time_start = etree.SubElement(chapter_atom, "ChapterTimeStart")
            chapter_time_start.text = chapter_entry.time_str
            chapter_flag_hidden = etree.SubElement(chapter_atom, "ChapterFlagHidden")
            chapter_flag_hidden.text = "0"
            chapter_flag_enabled = etree.SubElement(chapter_atom, "ChapterFlagEnabled")
            chapter_flag_enabled.text = "1"
            chapter_display = etree.SubElement(chapter_atom, "ChapterDisplay")
            chapter_string = etree.SubElement(chapter_display, "ChapterString")
            if chapter_entry.name:
                chapter_string.text = chapter_entry.name
            else:
                chapter_string.text = f"Chapter {index + 1:02d}"
            chapter_language = etree.SubElement(chapter_display, "ChapterLanguage")
            chapter_language.text = chapter_entry.language

    def export(self, destination, overwrite=False):
        if os.path.exists(destination) and not overwrite:
            raise FileExistsError()
        os.makedirs(os.path.dirname(destination), exist_ok=True)
        with open(destination, "wb") as f:
            f.write(etree.tostring(self.xml_chapter, encoding="utf-8",
                                   doctype='<!DOCTYPE Chapters SYSTEM "matroskachapters.dtd">',
                                   xml_declaration=True,
                                   pretty_print=True))


class ChapterEntry:
    def __init__(self, time_sec, language="eng", name=None):
        assert time_sec >= 0.
        assert len(language) == 3
        self._time_sec = time_sec
        self.language = language
        self.name = name

    @property
    def time_sec(self):
        return self._time_sec

    @time_sec.setter
    def time_sec(self, value):
        if value < 0.:
            raise ValueError("Time stamp of a chapter cannot be negative.")
        self._time_sec = value

    @property
    def time_str(self):
        seconds = self.time_sec
        hour = int(seconds) // 3600
        seconds %= 3600
        minute = int(seconds) // 60
        seconds %= 60
        seconds_int = int(seconds)
        seconds_decimals = int((seconds % 1) * 10 ** 6)
        return f"{hour:02d}:{minute:02d}:{seconds_int:02d}.{seconds_decimals:06d}"

    def __str__(self):
        return f"{self.time_str}\t{self.language}" + (f"{self.name}" if self.name else "")

    def __repr__(self):
        return f"ChapterEntry({self.time_str}, {self.language}, {self.name})"


class Chapter:
    def __init__(self, data=None, end_time=None):
        if not data:
            self.data = []
        else:
            self.data = data
        self._end_time = end_time
        self.check_data()

    @property
    def end_time(self):
        return self._end_time

    @end_time.setter
    def end_time(self, value):
        for c in self.data:
            if value < c.time_sec:
                raise ValueError("End time of the stream must be larger than all chapters.")
        self._end_time = value

    @classmethod
    def from_mpls(cls, filename):
        """

        Args:
            filename: filename of the mpls file

        Returns:
            A list of tuples, [(play_item_ID: int, chapters: Chapter)..]
        """
        mpls = MoviePlaylist(filename)
        result = []
        play_items = mpls.data["PlayList"]["PlayItems"]
        playlist_marks = mpls.data["PlayListMark"]["PlayListMarks"]
        playlist_marks_dict = {}
        for playlist_mark in playlist_marks:
            # entry-mark
            if playlist_mark["MarkType"] == 1:
                ref_to_pi = playlist_mark["RefToPlayItemID"]
                time_raw = playlist_mark["MarkTimeStamp"]
                if ref_to_pi in playlist_marks_dict:
                    playlist_marks_dict[ref_to_pi].append(time_raw)
                else:
                    playlist_marks_dict[ref_to_pi] = [time_raw]
        for play_item_index, play_item in enumerate(play_items):
            if play_item_index not in playlist_marks_dict:
                continue
            in_time = play_item["INTime"]
            end_time = (play_item["OUTTime"] - in_time) / 45000
            chapter_data = []
            first_chapter_time = playlist_marks_dict[play_item_index][0] - in_time
            if first_chapter_time > 0:
                chapter_data.append(ChapterEntry(0.))
            if first_chapter_time < 0:
                raise ValueError("First chapter time is earlier than play item in-time, this is considered an error.")

            for raw_time in playlist_marks_dict[play_item_index]:
                chapter_data.append(ChapterEntry((raw_time - in_time) / 45000))

            result.append((play_item["ClipInformationFileName"], Chapter(chapter_data, end_time)))

        return result

    def check_data(self):
        assert isinstance(self.data, list)
        # the first chapter must always be at the beginning
        if self.data:
            assert self.data[0].time_sec == 0.
        for c in self.data:
            assert isinstance(c, ChapterEntry)

    def export(self, destination, export_format="xml"):
        if export_format == "xml":
            handler = MatroskaXMLChapter(self)
            handler.export(destination)
        else:
            raise NotImplementedError(f"Exporting chapters to format {export_format} is not supported yet.")

    def __getitem__(self, item):
        if isinstance(item, slice):
            indices = range(*item.indices(len(self.data)))
            # preserves all other attributes
            result = deepcopy(self)
            if len(indices) == 0:
                result.data = []
                return result
            new_data = []
            init_offset = self.data[indices[0]].time_sec
            for i in indices:
                new_chapter_entry = deepcopy(self.data[i])
                new_chapter_entry.time_sec -= init_offset
                new_data.append(new_chapter_entry)
            result.data = new_data
            result.end_time -= init_offset
            return result
        return self.data[item]

    def __add__(self, other):
        if isinstance(other, Chapter):
            # attributes will follow the current object, except for data and end_time
            result = deepcopy(self)
            new_offset = self.end_time
            for c in other.data:
                new_chapter_entry = deepcopy(c)
                new_chapter_entry.time_sec += new_offset
                result.data.append(new_chapter_entry)
            result.end_time += other.end_time
            return result
        elif isinstance(other, int) or isinstance(other, float):
            if other == 0.:
                return self
            else:
                raise NotImplementedError()
        else:
            raise ValueError()

    def __radd__(self, other):
        return self.__add__(other)

    def __repr__(self):
        return f"Chapter({self.data}, {self.end_time})"
