# -*- coding: ISO-8859-1 -*-
#############################################
## (C)opyright by Dirk Holtwick, 2002-2007 ##
## All rights reserved                     ##
#############################################

__reversion__ = "$Revision: 20 $"
__author__    = "$Author: holtwick $"
__date__      = "$Date: 2007-10-09 12:58:24 +0200 (Di, 09 Okt 2007) $"

import getopt
import sys
import os
import os.path
import glob
import urllib2
import urlparse
import tempfile
    
from pisa_version import *
from pisa_document import *
from pisa_util import log
from pisa_default import DEFAULT_CSS

__version__ = VERSION

# Backward compatibility
CreatePDF = pisaDocument

USAGE = (VERSION_STR + """

USAGE: pisa [options] <src> <dest>

<src>
  Name of a HTML file or a file pattern using * placeholder.
  If you want to read from stdin use "-" as file name.
  You may also load an URL over HTTP. Take care of putting
  the <src> in quotes if it contains characters like "?". 

<dest>
  Name of the generated PDF file or "-" if you like
  to send the result to stdout. Take care that the
  destination file is not alread opened by an other
  application like the Adobe Reader. If the destination is
  not writeable a similar name will be calculated automatically.

[options]
  --css, -c:
    Path to default CSS file
  --css-dump:
    Dumps the default CSS definitions to STDOUT
  --debug, -d:
    Show debugging informations
  --encoding:
    the character encoding of <src>. If left empty (default) this 
    information will be extracted from the HTML header data         
  --help, -h:
    Show this help text
  --quiet, -q:
    Show no messages
  --start-viewer, -s:
    Start PDF default viewer on Windows and MacOSX
    (e.g. AcrobatReader)
  --version:
    Show version information 
  --warn, -w:
    Show warnings
  --xml, --xhtml, -x:
    Force parsing in XML Mode 
    (automatically used if file ends with ".xml")
  --html:
    Force parsing in HTML Mode (default) 
""").strip()

COPYRIGHT = VERSION_STR

LOG_FORMAT = "%(levelname)s [%(name)s] %(message)s"
LOG_FORMAT_DEBUG = "%(levelname)s [%(name)s] %(pathname)s line %(lineno)d: %(message)s"

#def options():
#    from optparse import OptionParser
#    usage = "usage: %prog [options] arg"
#    description = """
#    Converts HTML/XHTML/XML/CSS to PDF using the Reportlab Toolkit.
#    """.strip()
#    version = VERSION_STR
#    parser = OptionParser(
#        usage,
#        description=description,
#        version=version,
#        )    
#    parser.add_option(
#        "-c", "--css", 
#        help="Path to default CSS file",
#        dest="css",        
#        )
#    parser.add_option("-q", "--quiet",
#                      action="store_false", dest="verbose", default=True,
#                      help="don't print status messages to stdout")
#    parser.set_defaults(
#        css=None,
#        )
#    (options, args) = parser.parse_args()
#    if len(args) != 1:
#        parser.error("incorrect number of arguments")
#
#    print options, args

def usage():
    print USAGE

class pisaLinkLoader:

    """
    Helper to load page from an URL and load corresponding
    files to temporary files. If getFileName is called it 
    returns the temporary filename and takes care to delete
    it when pisaLinkLoader is unloaded. 
    """
    
    def __init__(self, src, quiet=True):
        self.quiet = quiet
        self.src = src
        self.tfileList = []
    
    def __del__(self):
        for path in self.tfileList:
            # print "DELETE", path
            os.remove(path)
            
    def getFileName(self, name, relative=None):
        try:
            url = urlparse.urljoin(relative or self.src, name)            
            suffix = urlparse.urlsplit(url)[2].split(".")[-1]
            if suffix.lower() not in ("css", "gif", "jpg", "png"):
                return None
            ufile = urllib2.urlopen(url)            
            path = tempfile.mktemp(suffix = "." + suffix)
            tfile = file(path, "wb")
            while True:
                data = ufile.read(1024)
                if not data:
                    break
                # print data
                tfile.write(data)
            ufile.close()
            tfile.close()
            self.tfileList.append(path)
            if not self.quiet:
                print "  Loading", url, "to", path
            return path
        except Exception, e:
            if not self.quiet:
                print "  ERROR:", e
            log.exception("pisaLinkLoader.getFileName")
        return None
    
def command():    
#    from optparse import OptionParser
#
#    parser = OptionParser()
#    parser.add_option("-f", "--file", dest="filename",
#                      help="write report to FILE", metavar="FILE")
#    parser.add_option("-q", "--quiet",
#                      action="store_false", dest="verbose", default=True,
#                      help="don't print status messages to stdout")
#    (options, args) = parser.parse_args()

    try:
        opts, args = getopt.getopt(sys.argv[1:], "dhqstwcx", [
            "quiet",
            "help",
            "start-viewer",
            "start",
            "debug=",
            "copyright",
            "version",
            "warn",
            #"booklet=",
            #"multivalent=",
            #"multivalent-path=",            
            "tempdir=",
            "format=",
            "css=",
            "css-dump",
            "xhtml",
            "xml",
            "html",
            "encoding=",
            ])
    except getopt.GetoptError:
        usage()
        sys.exit(2)

    errors = 0
    startviewer = 0
    quiet = 0    
    debug = 0
    warn = 0
    #multivalent_path = ""
    #booklet = ""   
    tempdir = None
    format = "pdf"
    css = None
    xhtml = None
    encoding = None
    
    log_level = logging.ERROR
    log_format = LOG_FORMAT

    for o, a in opts:
        
        if o in ("-h", "--help"):
            # Hilfe anzeigen
            usage()
            sys.exit()

        if o in ("-s", "--start-viewer", "--start"):
            # Anzeigeprogramm starten
            startviewer = 1

        if o in ("-q", "--quiet"):
            # Output unterdrücken
            quiet = 1

        if o in ("-w", "--warn"):
            # Warnings
            warn = 1
            log_level = min(log_level, logging.WARN) # If also -d ignore -w
            
        if o in ("-d", "--debug"):
            # Debug
            log_level = logging.DEBUG
            log_format = LOG_FORMAT_DEBUG
            # debug = 10
            if a:                
                log_level = int(a)

#        if o in ("--multivalent", "--multivalent-path"):
#            # Multivalent.jar für Booklet
#            multivalent_path = a

#        if o in ("--booklet",):
#            # Booklet
#            booklet = a

        if o in ("--copyright", "--version"):
            print COPYRIGHT
            sys.exit(0)

#        if o in ("--tempdir",):
#            # Tempdir
#            tempdir = a

        if o in ("-t", "--format"):
            # Format XXX ???
            format = a

        if o in ("--encoding",) and a:
            # Encoding
            encoding = a

        if o in ("-c", "--css"):
            # CSS
            # css = "@import url('%s');" % a
            css = file(a, "r").read()

        if o in ("--css-dump",):
            # CSS dump
            print DEFAULT_CSS
            return 

        if o in ("-x", "--xml", "--xhtml"):
            xhtml = True        
        elif o in ("--html",):
            xhtml = False        

    if not quiet:
        try:
            logging.basicConfig(
                level=log_level, 
                format=log_format)
        except:
            # XXX Logging doesn't work for Python 2.3 
            logging.basicConfig()
            
    if len(args) not in (1, 2):
        usage()
        sys.exit(2)

    if len(args)==2:
        a_src, a_dest = args
    else:
        a_src = args[0]
        a_dest = None
        
    if "*" in a_src:
        a_src = glob.glob(a_src)
        # print a_src
    else:
        a_src = [a_src]
    
    for src in a_src:
    
        # If not forced to parse in a special way have a look 
        # at the filename suffix
        if xhtml is None:
            xhtml = src.lower().endswith(".xml")
    
        lc = None
        wpath = None
        
        if src=="-":
            # Output to console
            fsrc = sys.stdin
            wpath = os.getcwd()
        else:
            # fsrc = open(src, "r")
            if src.startswith("http:"):
                wpath = src
                fsrc = urllib2.urlopen(src)
                lc = pisaLinkLoader(src, quiet=quiet).getFileName                
                src = "".join(urlparse.urlsplit(src)[1:3]).replace("/", "-")                                
            else:
                fsrc = wpath = os.path.abspath(src)
                fsrc = open(fsrc, "rb")

        if a_dest is None:
            dest_part = src            
            if dest_part.lower().endswith(".html") or dest_part.lower().endswith(".htm"):
                dest_part = ".".join(src.split(".")[:-1])
            dest = dest_part + "." + format.lower()
            for i in range(10):
                try:
                    open(dest, "wb").close()
                    break
                except:
                    pass
                dest = dest_part + "-%d.%s" % (i, format.lower())
        else:
            dest = a_dest
                
        fdestclose = 0
        
        if dest=="-":
            if sys.platform == "win32":
                import msvcrt
                msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)
            fdest = sys.stdout
            startviewer = 0
        else:
            dest = os.path.abspath(dest)
            try:
                open(dest, "wb").close()
            except:
                print "File '%s' seems to be in use of another application." % dest
                sys.exit(2)
            fdest = open(dest, "wb")
            fdestclose = 1
    
        if not quiet:
            print "Converting %s to %s..." % (src, dest)          
    
        pdf = pisaDocument(
            fsrc,
            fdest,
            debug = debug,
            path = wpath,
            errout = sys.stdout,
            #multivalent_path = multivalent_path,
            #booklet = booklet,
            tempdir = tempdir,
            format = format,
            link_callback = lc,
            default_css = css,
            xhtml = xhtml,
            encoding = encoding,
            )
    
        if fdestclose:
            fdest.close()
    
        errors += pdf.err
    
        if not quiet:
    
            #if pdf.log and (pdf.err or (pdf.warn and warn)):
            #    for mode, line, msg, code in pdf.log:
            #        print "%s in line %d: %s" % (mode, line, msg)
        
            if pdf.err:
                print "*** %d ERRORS OCCURED" % pdf.err
                    
        if (not pdf.err) and startviewer:
            if not quiet:
                print "Open viewer for file %s" % dest
            startViewer(dest)
    
    if errors:
        sys.exit(1)

def startViewer(filename):
    " Helper for opening a PDF file"
    try:
        os.startfile(filename)
    except:
        # try to opan a la apple
        os.system('open "%s"' % filename)

def showLogging(debug=False):
    " Shortcut for enabling log dump "
    try:
        log_level = logging.WARN
        log_format = LOG_FORMAT_DEBUG
        if debug:
            log_level = logging.DE
        logging.basicConfig(
            level=log_level,
            format=log_format)
    except:   
        logging.basicConfig()

if __name__=="__main__":
    command()
