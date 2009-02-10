# -*- coding: ISO-8859-1 -*-
#############################################
## (C)opyright by Dirk Holtwick, 2002-2008 ##
## All rights reserved                     ##
#############################################

"""
Updates the version infos
"""

import time
import re

VERSION = open("VERSION.txt", "r").read().strip()
BUILD = time.strftime("%Y-%m-%d %H:%M")
FILES = [
    "setup.py",
    # "setup_egg.py",
    "sx/pisa3/pisa_version.py",
    "doc\pisa-en.html",
    ]

rxversion = re.compile("VERSION{.*?}VERSION", re.MULTILINE|re.IGNORECASE|re.DOTALL)
rxbuild = re.compile("BUILD{.*?}BUILD", re.MULTILINE|re.IGNORECASE|re.DOTALL)
rxversionhtml = re.compile("\<\!--VERSION--\>.*?\<\!--VERSION--\>", re.MULTILINE|re.IGNORECASE|re.DOTALL)

for fname in FILES:
    data = open(fname, "rb").read()
    data = rxversion.sub("VERSION{" + VERSION + "}VERSION", data)
    data = rxversionhtml.sub("<!--VERSION-->" + VERSION + "<!--VERSION-->", data)
    data = rxbuild.sub("BUILD{" + BUILD + "}BUILD", data)
    open(fname, "wb").write(data)
