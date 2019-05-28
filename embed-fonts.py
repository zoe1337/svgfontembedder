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
    "--input",
    type=str,
    help="The SVG file you want to embed your fonts into.",
    required=True,
)
parser.add_argument(
    "--output",
    type=str,
    help="The SVG file to write.",
    required=True,
)

args = parser.parse_args()
infile = args.input
outfile = args.output

with open(infile) as fp:
    dom = bs4.BeautifulSoup(fp, features="xml")

print("Building font list...")
fontlist = []
for tag in dom.find_all('text'):
    for style in (tag["style"]).split(';'):
        if style[0:12] == "font-family:":
            fontname = style[12:]
            fontlist.append(fontname.replace("'", "").strip())

fontset = set(fontlist)
fontdict = {}
print(fontset)
print("Searching for fonts...")

for directory in fontdirs:
    filelist = []
    for root, directories, files in os.walk(directory):
        for fontfile in files:
            if '.otf' in fontfile or '.ttf' in fontfile:
                filelist.append(os.path.join(root, fontfile))

    for fontfile in filelist:
        if len(fontset) == 0:
            continue
        tt = ttLib.TTFont(fontfile)
        fontname, fontfamily = shortName(tt)
#        print("File %s contains %s" % (fontfile, fontname))
        if fontname in fontset or fontfamily in fontset:
            fontdict[fontfamily] = fontfile
#            print("Using %s from %s" % (fontname, fontfile))
            fontset.remove(fontfamily)

print(fontdict)

#print("Converting fonts to WOFF")

print("Embedding font data...")
fontdata = ""
for fontfam in fontdict:
    fontdata = fontdata + getFontAsString( fontdict[fontfam], fontfam )
styletag = dom.new_tag("style")
styletag.string = bs4.element.CData(fontdata)
dom.svg.insert(1, styletag)

print("Writing SVG...")
output_svg = open(outfile, "w")
output_svg.write(str(dom.prettify(formatter="none")))
output_svg.close()
