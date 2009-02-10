# -*- coding: ISO-8859-1 -*-
#############################################
## (C)opyright by Dirk Holtwick, 2002-2007 ##
## All rights reserved                     ##
#############################################

__reversion__ = "$Revision: 221 $"
__author__    = "$Author: holtwick $"
__date__      = "$Date: 2008-05-31 18:56:27 +0200 (Sa, 31 Mai 2008) $"

REQUIRED_INFO = """
****************************************************
IMPORT ERROR!
%s
****************************************************

The following Python packages are required for PISA:
- ReportlabToolkit>=2.1 <http://www.reportlab.org/>
- HTML5lib <http://code.google.com/p/html5lib/>

Optional packages:
- pyPDF <http://pybrary.net/pyPdf/>
- PIL <http://www.pythonware.com/products/pil/>

""".lstrip()

try:
    from pisa import *
except ImportError, e:
    import sys
    sys.stderr.write(REQUIRED_INFO % e)
    raise

__version__   = VERSION
