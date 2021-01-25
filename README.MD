# Shinya

Shinya(Shi'nya, not Shin'ya) is a python package to programmatically edit BDMV components like MPLS, CLPI, etc. It also includes scripts for common purposes.

## Documentation
Documentation will be available after more development progress is made. Currently, please consult the scripts and the source code for usages.

## Installation
Clone and cd into the repository directory, then run:
```bash
pip install -e .
```
or directly from `pypi`:
```bash
pip install shinya
```
With the second method, you need to download the scripts (and place them anywhere) separately if you need them.

## Feature and Todo List
 - [x] MPLS parsing, editing and saving
 - [x] CLPI parsing, editing and saving
 - [x] Index Table parsing, editing and saving
 - [x] Movie Object parsing, editing and saving
 - [ ] Extension data parsing, editing and saving
 - [x] Chapter slicing, joining, importing (mpls) and exporting (xml)

## Scripts
The purposes of the scripts are briefly described in the usages, more documentation may be available in the future.

## References
 - https://github.com/lw/BluRay/wiki
 - https://code.videolan.org/videolan/libbluray
 - https://github.com/justdan96/tsMuxer
 - https://github.com/Guymer/PyGuymer3
 - https://gitlab.com/mbunkus/mkvtoolnix

