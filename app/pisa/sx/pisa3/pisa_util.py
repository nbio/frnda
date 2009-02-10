# -*- coding: ISO-8859-1 -*-
#############################################
## (C)opyright by Dirk Holtwick, 2002-2007 ##
## All rights reserved                     ##
#############################################

__reversion__ = "$Revision: 20 $"
__author__    = "$Author: holtwick $"
__date__      = "$Date: 2007-10-09 12:58:24 +0200 (Di, 09 Okt 2007) $"

from reportlab.lib.units import inch, cm
from reportlab.lib.styles import *
from reportlab.lib.enums import *
from reportlab.lib.colors import *
from reportlab.lib.pagesizes import *
from reportlab.pdfbase import pdfmetrics
from reportlab.platypus import *
from reportlab.platypus.flowables import Flowable
from reportlab.platypus.tableofcontents import TableOfContents
# from reportlab.platypus.para import Para, PageNumberObject, UNDERLINE, HotLink

import reportlab
import copy
import types
import os
import os.path
import pprint
import sys
import logging
import string 

if not(reportlab.Version[0] == "2" and reportlab.Version[2]>="1"):
    raise ImportError("Reportlab Version 2.1+ is needed!")
    
log = logging.getLogger("ho.pisa")

try: 
    import cStringIO as StringIO
except:
    import StringIO

try:
    import pyPdf
except:
    pyPdf = None
    
try:
    from reportlab.graphics import renderPM
except:
    renderPM = None

try:
    from reportlab.graphics import renderSVG
except:
    renderSVG = None

def ErrorMsg():
    """
    Helper to get a nice traceback as string
    """
    import traceback, sys, cgi
    type = value = tb = limit = None
    type, value, tb = sys.exc_info()
    list = traceback.format_tb(tb, limit) + traceback.format_exception_only(type, value)
    return "Traceback (innermost last):\n" + "%-20s %s" % (
        string.join(list[:-1], ""),
        list[-1])

def toList(value):
    if type(value) not in (types.ListType, types.TupleType):
        return [value]
    return list(value)

def _toColor(arg, default=None):
    '''try to map an arbitrary arg to a color instance'''
    if isinstance(arg, Color): return arg
    tArg = type(arg)
    if tArg in (types.ListType, types.TupleType):
        assert 3<=len(arg)<=4, 'Can only convert 3 and 4 sequences to color'
        assert 0<=min(arg) and max(arg)<=1
        return len(arg)==3 and Color(arg[0], arg[1], arg[2]) or CMYKColor(arg[0], arg[1], arg[2], arg[3])
    elif tArg == types.StringType:
        C = getAllNamedColors()
        s = arg.lower()
        if C.has_key(s): return C[s]
        try:
            return toColor(eval(arg))
        except:
            pass
    try:
        return HexColor(arg)
    except:
        if default is None:
            raise ValueError('Invalid color value %r' % arg)
        return default
    
def getColor(value, default=None):
    " Convert to color value "
    try:
        original = value
        if isinstance(value, Color):
            return value
        value = str(value).lower()       
        if value=="transparent" or value=="none":
            return default
        if value.startswith("#") and len(value)==4:
            value = "#" + value[1] + value[1] + value[2] + value[2] + value[3] + value[3]
        # XXX Throws illegal in 2.1 e.g. toColor('none'), 
        # therefore we have a workaround here 
        return _toColor(value) 
    except ValueError, e:
        log.warn("Unknown color %r", original)
    return default

def getBorderStyle(value):
    # log.debug(value)
    if value and (str(value).lower() not in ("none", "hidden")):
        return value
    return None

mm = cm / 10.0
dpi96 = (1.0 / 96.0 * inch)

_absSizeTable = {
    "xx-small" : 3./5.,
    "x-small": 3./4.,
    "small": 8./9.,
    "medium": 1./1.,
    "large": 6./5.,
    "x-large": 3./2.,
    "xx-large": 2./1.,
    "xxx-large": 3./1.,
    "larger": 1.25,
    "smaller": 0.75,
    }

def getSize(value, relative=0):
    """
    Converts strings to standard sizes   
    """
    try:
        original = value
        if value is None:
            return relative
        elif type(value) is types.FloatType:
            return value
        elif type(value) is types.IntType:
            return float(value)
        elif type(value)==types.TupleType:
            value = "".join(value)
            
        value = str(value).strip().lower().replace(",", ".")    
        if value[-2:]=='cm': 
            return float(value[:-2].strip()) * cm
        elif value[-2:]=='mm': 
            return (float(value[:-2].strip()) * mm) # 1mm = 0.1cm
        elif value[-2:]=='in': 
            return float(value[:-2].strip()) * inch # 1pt == 1/72inch
        elif value[-2:]=='inch': 
            return float(value[:-4].strip()) * inch # 1pt == 1/72inch
        elif value[-2:]=='pt': 
            return float(value[:-2].strip())
        elif value[-2:]=='pc': 
            return float(value[:-2].strip()) * 12.0 # 1pt == 12pt
        elif value[-2:]=='px': 
            return float(value[:-2].strip()) * dpi96 # XXX W3C says, use 96pdi http://www.w3.org/TR/CSS21/syndata.html#length-units
        elif value[-1:]=='i':  # 1pt == 1/72inch
            return float(value[:-1].strip()) * inch
        elif value[-2:]=='em': # XXX
            return (float(value[:-2].strip()) * relative) # 1em = 1 * fontSize
        elif value[-2:]=='ex': # XXX
            return (float(value[:-2].strip()) * 2.0) # 1ex = 1/2 fontSize
        elif value[-1:]=='%': 
            # print "%", value, relative, (relative * float(value[:-1].strip())) / 100.0
            return (relative * float(value[:-1].strip())) / 100.0 # 1% = (fontSize * 1) / 100
        elif value in ("normal", "inherit"):
            return relative
        elif value in ("none", "0", "auto"):
            return 0.0
        elif _absSizeTable.has_key(value):
            return relative * _absSizeTable[value] 
        return float(value)
    except Exception, e:
        log.warn("getSize %r %r", original, relative, exc_info=1)
        # print "ERROR getSize", repr(value), repr(value), e        
        return 0.0
    
def getCoords(x, y, w, h, pagesize):
    """
    As a stupid programmer I like to use the upper left
    corner of the document as the 0,0 coords therefore
    we need to do some fancy calculations
    """
    #~ print pagesize
    ax, ay = pagesize
    if x < 0:
        x = ax + x
    if y < 0:
        y = ay + y
    if w != None and h != None:
        if w <= 0:
            w = (ax - x + w)
        if h <= 0:
            h = (ay - y + h)
        return x, (ay - y - h), w, h
    return x, (ay - y)

def getBox(s, pagesize):
    """
    Parse sizes by corners in the form: 
    <X-Left> <Y-Upper> <Width> <Height>
    The last to values with negative values are interpreted as offsets form
    the right and lower border.
    """
    l = s.split()
    if len(l)<>4:
        raise Exception, "box not defined right way"
    x, y, w, h = map(getSize, l)
    return getCoords(x, y, w, h, pagesize)

def getPos(s, pagesize):
    """
    Pair of coordinates
    """
    l = string.split(s)
    if len(l)<>2:
        raise Exception, "position not defined right way"
    x, y = map(getSize, l)
    return getCoords(x, y, None, None, pagesize)

def getBool(s):
    " Is it a boolean? "
    return str(s).lower() in ("y", "yes", "1", "true")

_uid = 0
def getUID():
    " Unique ID "
    global _uid
    _uid += 1
    return str(_uid)

_alignments = {
    "left": TA_LEFT,
    "center": TA_CENTER,
    "middle": TA_CENTER,
    "right": TA_RIGHT,
    "justify": TA_JUSTIFY,
    }

def getAlign(value):
    return _alignments.get(value.lower(), TA_LEFT)

def getVAlign(value):
    # Unused
    return value.upper()

