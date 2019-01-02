#!python
"""
Export selected layers from Inkscape SVG to PNG.
"""

from xml.dom import minidom
import codecs
import sys
from optparse import OptionParser
import os
import logging
import subprocess
from tqdm import tqdm

# logging setup
handler = logging.StreamHandler(stream=sys.stdout)
formatter = logging.Formatter(fmt="%(asctime)s %(levelname)s: %(message)s")
handler.setFormatter(formatter)
logger = logging.Logger(name=__file__, level=logging.WARN)
logger.addHandler(handler)


class Exporter(object):
    def __init__(self, source=None, output=None, dpi=90, keep_svg=False):
        self.source = source
        self.output_dir = output
        self.dpi = dpi
        self.keep_svg = keep_svg
        self.inkscape_exe = "C:/Program Files (x86)/Inkscape/inkscape.exe"

        if not os.path.exists(os.path.abspath(self.output_dir)):
            os.mkdir(os.path.abspath(self.output_dir))
            logging.info("created output directory %s" % os.path.abspath(self.output_dir))

        path, file = os.path.split(os.path.abspath(self.source))
        self.sourcename, self.ext = os.path.splitext(file)

    def process(self):

        svg = minidom.parse(open(self.source))

        g_base = None
        g_render = list()

        # find all layers
        for g in svg.getElementsByTagName("g"):
            if not "inkscape:groupmode" in g.attributes.keys():
                continue
            if not g.attributes["inkscape:groupmode"].value == "layer":
                continue
            if "inkscape:label" in g.attributes.keys():
                label = g.attributes["inkscape:label"].value
                if "base" in str(label).lower():
                    g_base = g
                else:
                    g_render.append(g)

        # may be we found no base layer..
        if g_base is None:
            logger.error("Failed to find Base-Layer.. quitting!")
            exit()

        for i in tqdm(range(len(g_render))):

            svg = minidom.parse(open(self.source))
            root = svg.documentElement

            for g in svg.getElementsByTagName("g"):
                if not "inkscape:groupmode" in g.attributes.keys():
                    continue
                if not g.attributes["inkscape:groupmode"].value == "layer":
                    continue
                if "inkscape:label" in g.attributes.keys():
                    label = str(g.attributes["inkscape:label"].value).lower()
                    if g_base.attributes["inkscape:label"].value == label:
                        # display base layer always
                        g.attributes['style'] = "display:inline"
                    else:
                        if g_render[i].attributes["inkscape:label"].value == label:
                            # keep it
                            g.attributes['style'] = "display:inline"
                        else:
                            logger.debug("attributes: %s" % str(g.attributes.keys()))
                            for attr in g.attributes.keys():
                                logger.debug("%s -> %s" % (attr, g.attributes[attr].value))
                            logger.debug("removing %s" % str(g.attributes["inkscape:label"].value))
                            # remove it
                            root.removeChild(g)

            export = svg.toxml()

            label = g_render[i].attributes["inkscape:label"].value
            pngfile = str("%s_%s_%ddpi.png" % (self.sourcename, label, self.dpi))
            svgfile = str("%s_%s.svg" % (self.sourcename, label))

            codecs.open(os.path.join(os.path.abspath(self.output_dir), svgfile), "w", encoding="utf8").write(export)

            inkscape_export_command = [
                self.inkscape_exe,
                "--without-gui",
                "--export-area-page",  # TODO: plug in the mode from options
                "--export-png=%s" % os.path.join(self.output_dir, pngfile),
                "--export-dpi=%d" % self.dpi,
                #"-b 0xffffffff",
                os.path.join(os.path.abspath(self.output_dir), svgfile)
            ]

            shell_output = subprocess.check_output(inkscape_export_command)
            logger.debug("----- Inkscape-Output -----\n\n%s" % shell_output.decode())

            if not self.keep_svg:
                os.remove(os.path.join(os.path.abspath(self.output_dir), svgfile))


if __name__ == "__main__":

    parser = OptionParser()
    parser.add_option("-i", "--input", dest="input", help="input file to process", metavar="FILE")
    parser.add_option("-o", "--output", dest="output", help="output directory", metavar="OUTDIR")
    parser.add_option("-k", "--keepsvg", dest="keep_svg", help="keep svg file", action="store_true")
    parser.add_option("-d", "--dpi", dest="dpi", help="specify resolution in dpi, e.g. --dpi 90", type=int, default=90)
    parser.add_option("-v", "--verbose", dest="verbose", help="enable debug output", action="store_true", default=False)
    # parser.add_option("-l", "--layers", dest="layers", help="the layers to export, e.g. --layers foo,bar,baz")
    # parser.add_option("-m", "--mode", dest="mode", help="select mode, e.g. --mode page (default)", default="page")
    # parser.add_option("-r", "--resolution", dest="resolution", help="specify resolution in px, e.g. --resolution 80x80")

    (options, args) = parser.parse_args()

    if options.verbose:
        logger.setLevel(logging.DEBUG)

    logger.debug("Raw Arguments: %s" % sys.argv)

    if options.output is None or options.input is None:
        logger.error("params input and output are required!")
        parser.print_help()
        exit()

    e = Exporter(source=options.input, output=options.output, dpi=options.dpi, keep_svg=options.keep_svg)
    e.process()
