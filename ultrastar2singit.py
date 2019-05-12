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
    with open("titleid/romfs/Songs/vxla/" + filename, "wb") as f:
        f.write(xmlstr)


def load_from_youtube(url, name):
    yt = "youtube-dl " + url + \
        " --write-thumbnail --recode-video mp4 --postprocessor-args '-vf fps=fps=25,scale=1280x720 -c:v libx264 -x264opts nal-hrd=cbr:force-cfr=1 -b:v 1415k -minrate 1415k -maxrate 1415k' --output 'tmp/" + \
        name + ".%(ext)s'"
    os.system(yt)
    os.system("ffmpeg -i " + "tmp/" + name +
              ".mp4 -vn -acodec libvorbis " + "tmp/" + name + ".ogg")
    os.system("ffmpeg -i tmp/" + name +
              ".mp4 -vcodec copy -an " + name + "no_audio.mp4 ")
    os.rename("tmp/" + name + "no_audio.mp4",
              "titleid/romfs/Songs/videos/" + name + ".mp4")
    shutil.copyfile("tmp/" +
                    name + ".ogg", "titleid/romfs/Songs/audio_preview/" + name + "_preview.ogg")
    os.rename("tmp/" + name + ".ogg",
              "titleid/romfs/Songs/audio/" + name + ".ogg")
    im = Image.open("tmp/" + name + '.jpg')
    im.save("titleid/romfs/Songs/covers/" + name + ".png")


def mkdirs():
    os.makedirs("titleid/romfs/Songs/audio", exist_ok=True)
    os.makedirs("titleid/romfs/Songs/audio_preview", exist_ok=True)
    os.makedirs("titleid/romfs/Songs/covers", exist_ok=True)
    os.makedirs("titleid/romfs/Songs/videos", exist_ok=True)
    os.makedirs("titleid/romfs/Songs/vxla", exist_ok=True)


parser = argparse.ArgumentParser()

parser.add_argument('song.txt',   help='Ultrastar text file')
parser.add_argument(
    '-p', type=int, help='pitch correction, default 48', default='48')

parser.add_argument(
    '-s', help='song to replace')

parser.add_argument(
    '-yt', help='youtube stream URL')

args = parser.parse_args()


input_file = getattr(args, 'song.txt')

us_data = parse_file(input_file)

if args.s:
    output_file = args.s
else:
    output_file = re.sub('[^A-Za-z0-9]+', '', us_data["TITLE"])

mkdirs()
sing_it = map_data(us_data, args.p)
write_vxla_file(sing_it, output_file + '.vxla')
if args.yt:
    load_from_youtube(args.yt, output_file)
