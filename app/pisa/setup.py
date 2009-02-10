#!/usr/bin/env python
# -*- coding: ISO-8859-1 -*-
#############################################
## (C)opyright by Dirk Holtwick, 2002-2008 ##
## All rights reserved                     ##
#############################################

try:
    from setuptools import setup
except ImportError:
    # log warning: cannot import setuptools, switching to distutils ?
    from distutils.core import setup

setup(
    name           = "pisa",
    version        = "VERSION{3.0.20}VERSION"[8:-8],
    description    = "PDF generator using HTML and CSS",
    license        = "Qt Public License (QPL)",
    author         = "Dirk Holtwick",
    author_email   = "holtwick@web.de",
    url            = "http://www.htmltopdf.org/",
    download_url   = "http://www.htmltopdf.org/download.html",
    keywords       = "HTML, CSS, PDF",

    requires       = ["html5lib", "reportlab"],

    include_package_data = False,

    packages = [
        'ho',
        'ho.pisa',
        'sx',
        'sx.pisa3',
        'sx.w3c',
        ],

    test_suite = "sx",

    entry_points = {
        'console_scripts': ['pisa = sx.pisa3:command',]
        },

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
