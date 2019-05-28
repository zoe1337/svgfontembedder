# svgfontembedder
A Python program which embeds the used fonts into an SVG document

At the moment it only supports Linux, since I don't use other platforms and can't test it.

## Requirements
- BeautifulSoup4
- argparse
- fonttools

## How to use
From a terminal run `./embed-fonts.py --input <INPUT SVG FILE> --output <OUTPUT SVG FILE>`

## How does it work
The program parses the input SVG file, makes a list of the fonts used, and then scans local font directories, trying to find the source of the used font face.

Then it base64 codes and embeds the fonts into the SVG document, which gets a new &lt;style&gt; tag. Finally, it writes the output to the specified output file. It never modifies the source SVG file! 

## Limitations
Right now it ignores font-weight and other variant information, so italic and bold text won't work properly. :(

It can't always find every used font; it only supports TTF and OTF at the moment.
