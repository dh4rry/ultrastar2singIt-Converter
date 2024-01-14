import io
import xml.etree.cElementTree as ET
from xml.dom import minidom
import argparse
import sys
import re
import os
import shutil
from PIL import Image


def parse_file(filename):
    data = {"notes": []}
    with io.open(filename, "r", encoding="ISO-8859-1", errors='ignore') as f:
        for line in f:
            line = line.replace('\n', '')
            if line.startswith("#"):
                p = line.split(":", 1)
                if len(p) == 2:
                    data[p[0][1:]] = p[1]
            else:
                note_arr = line.split(" ", 4)
                data["notes"].append(note_arr)
    return data


def map_data(us_data, pitch_corr):
    sing_it = {"text": [], "notes": [], "pages": [], "notes_golden": []}
    bpm = float(us_data["BPM"].replace(',', '.'))
    gap = float(us_data["GAP"].replace(',', '.')) / 1000
    min_note = 1
    last_page = 0.0
    for note in us_data["notes"]:
        if note[0] == ":" or note[0] == "*":
            start = float(note[1]) * 60 / bpm / 4 + gap
            end = start + float(note[2]) * 60 / bpm / 4
            sing_it["text"].append({"t1": start, "t2": end, "value":  note[4]})
            nint = int(note[3])
            if nint < min_note:
                nint = min_note

            sing_it["notes"].append(
                {"t1": start, "t2": end, "value":  nint + pitch_corr})
            if note[0] == "*":
                sing_it["notes_golden"].append(
                    {"t1": start, "t2": end, "value":  nint + pitch_corr})
        elif note[0] == "-":
            start = last_page
            end = float(note[1]) * 60 / bpm / 4 + gap
            last_page = end
            sing_it["pages"].append(
                {"t1": start, "t2": end, "value": ""})
        elif note[0] == "E":
            if end > last_page:
                start = last_page
                sing_it["pages"].append(
                    {"t1": start, "t2": end, "value": ""})
    return sing_it


def write_intervals(interval_arr, parent):
    for interval in interval_arr:
        ET.SubElement(parent, "Interval",
                      t1="{0:.3f}".format(interval["t1"]), t2="{0:.3f}".format(interval["t2"]), value=str(interval["value"]))


def write_metadata_file(us_data, songname):
    root = ET.Element("DLCSong")
    root.set("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
    root.set("xmlns:xsd", "http://www.w3.org/2001/XMLSchema")
    ET.SubElement(root, "Genre").text = us_data.get("GENRE", "Rock")
    ET.SubElement(root, "Id").text = songname
    ET.SubElement(root, "Uid").text = "160"
    ET.SubElement(root, "Artist").text = us_data.get("ARTIST", "Unknown")
    ET.SubElement(root, "Title").text = us_data.get("TITLE", "Unknown")
    ET.SubElement(root, "Year").text = us_data.get("YEAR", "2000")
    ET.SubElement(root, "Ratio").text = "Ratio_16_9"
    ET.SubElement(root, "Difficulty").text = "Difficulty0"
    ET.SubElement(root, "Feat")
    ET.SubElement(root, "Line1").text = us_data.get("ARTIST", "Unknown")
    ET.SubElement(root, "Line2")
    xmlstr = minidom.parseString(ET.tostring(root)).toprettyxml(
        encoding="utf-8", indent="   ").decode('utf-8')
    xmlbin = xmlstr.replace('\n', '\r\n').encode('utf-8-sig')
    with open("titleid/romfs/" + songname + "_meta.xml", "wb") as f:
        f.write(xmlbin)


def write_vxla_file(sing_it, filename):
    root = ET.Element("AnnotationFile", version="2.0")

    doc = ET.SubElement(root, "IntervalLayer", datatype="STRING",
                        name="structure", units="", description="")
    ET.SubElement(doc, "Interval", t1="2.000", t2="3.000", value="couplet1")

    doc = ET.SubElement(root, "IntervalLayer", datatype="STRING",
                        name="shortversion", units="", description="")
    ET.SubElement(doc, "Interval", t1="0.000",
                  t2="60.000", value="shortversion")

    doc = ET.SubElement(root, "IntervalLayer", datatype="STRING",
                        name="lyrics", units="", description="")
    write_intervals(sing_it["text"], doc)

    doc = ET.SubElement(root, "IntervalLayer", datatype="STRING",
                        name="lyrics_cut", units="", description="")
    write_intervals(sing_it["text"], doc)

    doc = ET.SubElement(root, "IntervalLayer", datatype="UINT8",
                        name="notes", units="", description="")
    write_intervals(sing_it["notes"], doc)

    doc = ET.SubElement(root, "IntervalLayer", datatype="UINT8",
                        name="notes_golden", units="", description="")
    write_intervals(sing_it["notes_golden"], doc)

    doc = ET.SubElement(root, "IntervalLayer", datatype="STRING",
                        name="pages", units="", description="")
    write_intervals(sing_it["pages"], doc)
    xmlstr = minidom.parseString(ET.tostring(root)).toprettyxml(
        encoding="ISO-8859-1", indent="   ")
    with open(filename, "wb") as f:
        f.write(xmlstr)


parser = argparse.ArgumentParser()

parser.add_argument('song.txt',   help='Ultrastar text file')
parser.add_argument(
    '-p', type=int, help='pitch correction, default 48', default='48')

parser.add_argument(
    '-s', help='song to replace')

args = parser.parse_args()


input_file = getattr(args, 'song.txt')

us_data = parse_file(input_file)

if args.s:
    output_file = args.s
else:
    output_file = re.sub('[^A-Za-z0-9]+', '', us_data["TITLE"])

sing_it = map_data(us_data, args.p)
write_vxla_file(sing_it, output_file + '.vxla')
