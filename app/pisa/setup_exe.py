# -*- coding: ISO-8859-1 -*-
#############################################
## (C)opyright by Dirk Holtwick, 2002-2007 ##
## All rights reserved                     ##
#############################################

__version__ = "$Revision: 208 $"
__author__  = "$Author: holtwick $"
__date__    = "$Date: 2008-04-28 16:54:46 +0200 (Mo, 28 Apr 2008) $"
__svnid__   = "$Id: setup_exe.py 208 2008-04-28 14:54:46Z holtwick $"

"""
Optimiert für den Einsatz mit py2exe Version 0.5.4
"""

#import sys
#import sx.pisa3.pisa_version as version
#version.newBuild()
#version = reload(version)

#import sys
#sys.path.append("../html5lib/python/src")
#sys.path.append("../pypdf")
#sys.path.append("../reportlab_2_1")

#if len(sys.argv) == 1:
#    sys.argv.append("py2exe")
#    sys.argv.append("-q")

#sys.path += [".."]

import zipfile
from distutils.core import setup
import py2exe

VERSION = "VERSION{3.0.18}VERSION"[8:-8]

class Target:
    def __init__(self, **kw):
        self.__dict__.update(kw)
        self.version = VERSION
        self.company_name = "Dirk Holtwick"
        self.copyright = "(c) Dirk Holtwick, 2008"
        self.name = "pisa"
        self.description = "pisa"

setup(

    console = [{
        'script': "pisa.py",
        }],

    options = {
        "py2exe": {
            # "optimize" : 2,
            "excludes" : ["Tkinter","Tix"],
            "includes": [
                "encodings",
                "encodings.*",
                'ho',
                'ho.pisa',
                "sx",
                "sx.pisa3",
                "sx.w3c",
                "html5lib",
                "html5lib.treebuilders.*",
                "html5lib.treewalkers.*",
                "reportlab",
                ],
            "dist_dir" : "exe",
            "bundle_files": 1,
            }
        },

    name           = "pisa",
    version        = VERSION,
    description    = "PDF generator using HTML and CSS",
    license        = "Qt Public License (QPL)",
    author         = "Dirk Holtwick",
    author_email   = "holtwick@web.de",
    url            = "http://www.htmltopdf.org/",
    download_url   = "http://www.htmltopdf.org/download.html",
    keywords       = "HTML, CSS, PDF",

    requires       = ["html5lib", "reportlab"],

    packages       = [
        'sx',
        'sx.pisa3',
        'sx.w3c',
        ],


    long_description = """
pisa is a html2pdf converter using the ReportLab Toolkit,
the HTML5lib and pyPdf. It supports HTML 5 and CSS 2.1 (and some of CSS 3).
It is completely written in pure Python so it is platform independent.
The main benefit of this tool that a user with Web skills like HTML and CSS
is able to generate PDF templates very quickly without learning new
technologies. Easy integration into Python frameworks like CherryPy,
KID Templating, TurboGears, Django, Zope, Plone, etc. (see 'demo' folder for
examples)
        """.strip(),

    classifiers = [x.strip() for x in """
        Development Status :: 4 - Beta
        Environment :: Console
        Environment :: Web Environment
        Intended Audience :: Customer Service
        Intended Audience :: Developers
        Intended Audience :: Financial and Insurance Industry
        Intended Audience :: Healthcare Industry
        Intended Audience :: Information Technology
        Intended Audience :: Legal Industry
        Intended Audience :: Manufacturing
        Intended Audience :: Science/Research
        Intended Audience :: System Administrators
        Intended Audience :: Telecommunications Industry
        License :: Free for non-commercial use
        License :: OSI Approved :: Qt Public License (QPL)
        Natural Language :: English
        Natural Language :: German
        Operating System :: MacOS
        Operating System :: MacOS :: MacOS X
        Operating System :: Microsoft
        Operating System :: Microsoft :: MS-DOS
        Operating System :: Microsoft :: Windows
        Operating System :: Other OS
        Operating System :: POSIX
        Operating System :: POSIX :: Linux
        Operating System :: Unix
        Topic :: Documentation
        Topic :: Internet
        Topic :: Multimedia
        Topic :: Office/Business
        Topic :: Office/Business :: Financial
        Topic :: Office/Business :: Financial :: Accounting
        Topic :: Printing
        Topic :: Text Processing
        Topic :: Text Processing :: Fonts
        Topic :: Text Processing :: Markup
        Topic :: Text Processing :: Markup :: HTML
        Topic :: Text Processing :: Markup :: XML
        Topic :: Utilities
        """.strip().splitlines()],

)


import os, os.path, shutil

SDIST = "pisa-" + VERSION + "\\"
DIR = "pisa-" + VERSION + "-windows"
# os.makedirs(DIR)
os.rename("exe", DIR)
shutil.copy(r"LICENSE.txt", DIR)
shutil.copy(r"LICENSE.pdf", DIR)
shutil.copy(r"README-WINDOWS.TXT", DIR + "\\README.txt")
shutil.copytree(SDIST + "doc", DIR + "\\doc")
shutil.copytree(SDIST + "test", DIR + "\\test")
os.system(r"zip -r dist\pisa-windows.zip pisa-" + VERSION + "-windows")
