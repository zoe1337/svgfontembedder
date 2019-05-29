#!/usr/bin/env python3

import sys, os
import bs4 
import argparse
from fontTools import ttLib
import base64

homedir = os.getenv('HOME', '')
fontsdir = "homedir" + "/.local/share/fonts"
pwd = os.getenv('PWD', '')
gslib = os.getenv('GS_LIB', '')
sysfonts = "/usr/share/fonts"

fontdirs = [fontsdir, pwd, gslib, sysfonts]

# ------

mimetypes = {
    "otf": "application/vnd.ms-opentype",
    "ttf": "font/sfnt",
    "woff": "application/font-woff"
    }

FONT_SPECIFIER_NAME_ID = 4
FONT_SPECIFIER_FAMILY_ID = 1
def shortName( font ):
    """Get the short name from the font's names table"""
    name = ""
    family = ""
    for record in font['name'].names:
        if b'\x00' in record.string:
            name_str = record.string.decode('utf-16-be')
        else:   
            name_str = record.string.decode('latin-1')
        if record.nameID == FONT_SPECIFIER_NAME_ID and not name:
            name = name_str
        elif record.nameID == FONT_SPECIFIER_FAMILY_ID and not family: 
            family = name_str
        if name and family: break
    return name, family

def getFontAsString( fontfile, fontfamily ):
    mime = mimetypes[fontfile[-3:].lower()]
    f = open(fontfile, "rb")
    b64data = base64.b64encode(f.read())
    f.close()
    return "@font-face {\n font-family: '%s';\n src:url(\"data:%s;charset=utf-8;base64,%s\");\n}\n" % (fontfamily, mime, b64data.decode("ascii"))


# ------

parser = argparse.ArgumentParser(description="Embed fonts into SVG")

parser.add_argument(
    "input",
    type=argparse.FileType('r'),
    help="The SVG file you want to embed your fonts into.",
)
parser.add_argument(
    "output",
    type=argparse.FileType('w'),
    help="The SVG file to write.",
)
parser.add_argument(
    "--verbose", "-v",
    action="store_true",
    help="Show what's happening behind the curtains.",
)

args = parser.parse_args()
infile = args.input
outfile = args.output
debug = args.verbose

if outfile.name == infile.name:
    print("Error: input file and output file are identical.")
    sys.exit(2)

print("Reading document...")
dom = bs4.BeautifulSoup(infile, features="xml")

print("Building font list...", end='')
fontlist = []
for tag in dom.find_all('text'):
    for style in (tag["style"]).split(';'):
#        if debug:
#            if style[0:5] == "font-":
#                print("[i] SVG style: %s" % style)
        if style[0:12] == "font-family:":
            fontname = style[12:]
            fontlist.append(fontname.replace("'", "").strip())

fontset = list(set(fontlist))
print(" found %i unique fonts in the SVG." % len(fontset))

if debug:
    print(fontset)

print("Searching for fonts...", end='')
fontdb = []

for directory in fontdirs:
    filelist = []
    for root, directories, files in os.walk(directory):
        for fontfile in files:
            ext = fontfile[-3:].lower()
            if ext == 'otf' or ext == 'ttf':
                filelist.append(os.path.join(root, fontfile))

    for fontfile in filelist:
        tt = ttLib.TTFont(fontfile)
        fontname, fontfamily = shortName(tt)
#        if debug:
#            print("[i] File %s contains '%s' (font-family: %s)" % (fontfile, fontname, fontfamily))
        entry = {}
        entry["file"] = fontfile
        entry["name"] = fontname
        entry["family"] = fontfamily
        fontdb.append(entry)
print(" found %i fonts on the system." % len(fontdb))

if debug:
    print(fontdb)

print("Matching fonts...", end='')
fontdict = {}

for font in fontdb:
    fontname = font["name"]
    fontfile = font["file"]
    for current_font in fontset:
        if current_font == fontname:
            fontdict[current_font] = font["file"]
#            print("[!] Using '%s' as '%s' from %s" % (fontname, current_font, fontfile))
            fontset.remove(current_font)

for font in fontdb:
    fontname = font["family"]
    fontfile = font["file"]
    for current_font in fontset:
        if current_font == fontname:
            fontdict[current_font] = font["file"]
#            print("[!] Using '%s' as '%s' from %s" % (fontname, current_font, fontfile))
            fontset.remove(current_font)

for font in fontdb:
    fontname = font["family"]
    fontfile = font["file"]
    for current_font in fontset:
        if current_font in fontname:
            fontdict[current_font] = font["file"]
#            print("[!] Using '%s' as '%s' from %s" % (fontname, current_font, fontfile))
            fontset.remove(current_font)

print(" matched %i fonts." % len(fontdict))

if debug:
    print(fontdict)

print("Embedding font data...")
fontdata = ""
for fontfam in fontdict:
    fontdata = fontdata + getFontAsString( fontdict[fontfam], fontfam )
styletag = dom.new_tag("style")
styletag.string = bs4.element.CData(fontdata)
dom.svg.insert(1, styletag)

print("Writing SVG...")
outfile.write(str(dom.prettify(formatter="none")))
outfile.close()
