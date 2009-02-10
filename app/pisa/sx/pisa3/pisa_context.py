# -*- coding: utf-8 -*-
#############################################
## (C)opyright by Dirk Holtwick, 2002-2007 ##
## All rights reserved                     ##
#############################################

__reversion__ = "$Revision: 20 $"
__author__    = "$Author: holtwick $"
__date__      = "$Date: 2007-10-09 12:58:24 +0200 (Di, 09 Okt 2007) $"

from pisa_util import *
from pisa_reportlab import *

import pisa_default
import pisa_parser
import re
import urlparse
import types

from reportlab.platypus.paraparser import ParaParser, ParaFrag, ps2tt, tt2ps, ABag
from reportlab.platypus.paragraph import cleanBlockQuotedText
from reportlab.lib.styles import ParagraphStyle

import reportlab.rl_config
reportlab.rl_config.warnOnMissingFontGlyphs = 0

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.fonts import addMapping

from sx.w3c import css, cssDOMElementInterface

from html5lib.sanitizer import *

sizeDelta = 2       # amount to reduce font size by for super and sub script
subFraction = 0.4   # fraction of font size that a sub script should be lowered
superFraction = 0.4

def getParaFrag(style):   
    frag = ParaFrag()
    frag.sub = 0
    frag.super = 0
    frag.rise = 0
    frag.underline = 0 # XXX Need to be able to set color to fit CSS tests
    frag.strike = 0
    frag.greek = 0
    frag.link = None
    frag.text = ""
    
    # frag.lineBreak = 0
    #if bullet:
    #    frag.fontName, frag.bold, frag.italic = ps2tt(style.bulletFontName)
    #    frag.fontSize = style.bulletFontSize
    #    frag.textColor = hasattr(style,'bulletColor') and style.bulletColor or style.textColor
    #else:

    frag.fontName = "Times-Roman"
    frag.fontName, frag.bold, frag.italic = ps2tt(style.fontName)    
    frag.fontSize = style.fontSize
    frag.textColor = style.textColor
        
    # Extras
    frag.leading = 0
    frag.leadingSource = "150%"
    frag.backColor = white
    frag.borderWidth = 1
    frag.borderPadding = 0
    frag.borderColor = None
    frag.spaceBefore = 0
    frag.spaceAfter = 0
    frag.leftIndent = 0 
    frag.rightIndent = 0
    frag.firstLineIndent = 0
    frag.keepWithNext = False
    frag.alignment = TA_LEFT
    frag.vAlign = None
    
    frag.borderLeftWidth = 0
    frag.borderLeftColor = None
    frag.borderLeftStyle = None
    frag.borderRightWidth = 0
    frag.borderRightColor = None
    frag.borderRightStyle = None
    frag.borderTopWidth = 0
    frag.borderTopColor = None
    frag.borderTopStyle = None
    frag.borderBottomWidth = 0
    frag.borderBottomColor = None
    frag.borderBottomStyle = None

    frag.paddingLeft = 0
    frag.paddingRight = 0
    frag.paddingTop = 0
    frag.paddingBottom = 0

    frag.listStyleType = None
    frag.whiteSpace = "normal"
    
    frag.pageNumber = False
    frag.height = None
    frag.width = None

    frag.bulletIndent = 0
    frag.bulletText = None
    frag.bulletFontName = "Helvetica"
    frag.zoom = 1.0
    
    frag.outline = False
    frag.outlineLevel = 0
    frag.outlineOpen = False
    
    return frag     

def getDirName(path):
    if path and not path.lower().startswith("http:"):
        return os.path.dirname(os.path.abspath(path))
    return path

class pisaCSSBuilder(css.CSSBuilder):
    
    def atFontFace(self, declarations):
        " Embed fonts "
        result = self.ruleset([self.selector('*')], declarations)
        # print "@FONT-FACE", declarations, result
        try:
            data = result[0].values()[0]
            names = data["font-family"]

            # Font weight
            fweight = str(data.get("font-weight", "normal")).lower() 
            bold = fweight in ("bold", "bolder", "500", "600", "700", "800", "900")            
            if not bold and fweight<>"normal":   
                log.warn(self.c.warning("@fontface, unknown value font-weight '%s'", fweight))             
                
            # Font style
            italic = str(data.get("font-style", "")).lower() in ("italic", "oblique")            
            
            src = self.c.getFile(data["src"])
            self.c.loadFont(
                names,
                src,
                bold=bold,
                italic=italic)
        except Exception, e:
            log.warn(self.c.warning("@fontface"), exc_info=1)
        return {}, {}   
    
    def _pisaDimensions(self, data):
        " Calculate dimensions of a box "
        box = data.get("-pdf-frame-box", [])
        # print 123, box
        if len(box)==4:            
            return [getSize(x) for x in box]
        
        top = getSize(data.get("top", 0))
        left = getSize(data.get("left", 0))
        bottom = -getSize(data.get("bottom", 0))
        right = -getSize(data.get("right", 0))
        width = getSize(data.get("width", 0))
        height = getSize(data.get("height", 0))
        if height:            
            if (not top) and bottom:
                top = bottom - height
            else:
                bottom = top + height
        if width:              
            if (not left) and right:
                left = right - width
            else:
                right = left + width
        top += getSize(data.get("margin-top", 0))
        left += getSize(data.get("margin-left", 0))    
        bottom -= getSize(data.get("margin-bottom", 0))
        right -= getSize(data.get("margin-right", 0))
        # box = getCoords(left, top, width, height, self.c.pageSize)        
        # print "BOX", box
        return left, top, right, bottom
    
    def _pisaAddFrame(self, name, data, first=False, border=None):
        c = self.c            
        if not name:
            name = "-pdf-frame-%d" % c.UID()                
        x, y, w, h = self._pisaDimensions(data)
        # print name, x, y, w, h 
        #if not (w and h):
        #    return None 
        if first:
            return (
                name,
                None,
                data.get("-pdf-frame-border", border),
                x, y, w, h)
        return (
            name,
            data.get("-pdf-frame-content", None),
            data.get("-pdf-frame-border", border),
            x, y, w, h)
        
    def atPage(self, name, pseudopage, declarations):       
        try:

            c = self.c
            data = {}
            name = name or "body"
            pageBorder = None
            
            if declarations:            
                result = self.ruleset([self.selector('*')], declarations)
                # print "@PAGE", name, pseudopage, declarations, result
                                              
                if declarations:             
                    data = result[0].values()[0]
                    pageBorder = data.get("-pdf-frame-border", None)
                    for prop in [
                        "margin-top",
                        "margin-left",
                        "margin-right",
                        "margin-bottom",
                        "top",
                        "left",
                        "right",
                        "bottom",
                        "width",
                        "height"
                        ]:
                        if data.has_key(prop):                       
                            c.frameList.append(self._pisaAddFrame(name, data, first=True, border=pageBorder))
                            break                
                            
            if c.templateList.has_key(name):
                log.warn(self.warning("template '%s' has already been defined" % name))
                       
            if data.has_key("-pdf-page-size"):                
                c.pageSize = pisa_default.PML_PAGESIZES.get(str(data["-pdf-page-size"]).lower(), c.pageSize)
            
            if data.has_key("size"):                
                size = data["size"]
                # print size, c.pageSize
                if type(size) is not types.ListType:
                    size = [size]
                isLandscape = False
                sizeList = []
                for value in size:
                    valueStr = str(value).lower()
                    if type(value) is types.TupleType:
                        sizeList.append(getSize(value))
                    elif valueStr == "landscape":
                        isLandscape = True
                    elif pisa_default.PML_PAGESIZES.has_key(valueStr):
                        c.pageSize = pisa_default.PML_PAGESIZES[valueStr]
                    else:
                        log.warn(c.warning("Unknown size value for @page"))

                if len(sizeList) == 2:
                    c.pageSize = sizeList
                if isLandscape:
                    c.pageSize = landscape(c.pageSize)
            
            # self._drawing = PmlPageDrawing(self._pagesize)

            #if not c.frameList:                
            #    c.warning("missing frame definitions for template")
            #    return {}, {}

            # Frames have to be calculated after we know the pagesize
            frameList = []
            staticList = []            
            for fname, static, border, x, y, w, h in c.frameList:                
                x, y, w, h = getCoords(x, y, w, h, c.pageSize)
                if w<=0 or h<=0:
                    log.warn(self.c.warning("Negative width or height of frame. Check @frame definitions."))
                frame = Frame(
                    x, y, w, h,
                    id = fname,
                    leftPadding = 0,
                    rightPadding = 0,
                    bottomPadding = 0,
                    topPadding = 0,
                    showBoundary = border or pageBorder)
                if static:
                    frame.pisaStaticStory = []
                    c.frameStatic[static] = [frame] + c.frameStatic.get(static, [])
                    staticList.append(frame)
                else:
                    frameList.append(frame)        

            background = data.get("background-image", None)
            if background:
                background = c.getFile(background) 
            # print background
            
            # print frameList
            if not frameList:    
                # print 999            
                log.warn(c.warning("missing explicit frame definition for content or just static frames"))                
                fname, static, border, x, y, w, h = self._pisaAddFrame(name, data, first=True, border=pageBorder)           
                x, y, w, h = getCoords(x, y, w, h, c.pageSize)
                if w<=0 or h<=0:
                    log.warn(c.warning("Negative width or height of frame. Check @page definitions."))
                frameList.append(Frame(
                    x, y, w, h,
                    id = fname,
                    leftPadding = 0,
                    rightPadding = 0,
                    bottomPadding = 0,
                    topPadding = 0,
                    showBoundary = border or pageBorder))
                
            pt = PmlPageTemplate(
                id = name,
                frames = frameList,
                pagesize = c.pageSize,
                )             
            pt.pisaStaticList = staticList                        
            pt.pisaBackground = background
            pt.pisaBackgroundList = c.pisaBackgroundList
        
            # self._pagesize)
            # pt.pml_statics = self._statics
            # pt.pml_draw = self._draw
            # pt.pml_drawing = self._drawing
            # pt.pml_background = attrs.background
            # pt.pml_bgstory = self._bgstory
    
            c.templateList[name] = pt
            c.template = None
            c.frameList = []
            c.frameStaticList = []
        
        except Exception, e:            
            log.warn(self.c.warning("@page"), exc_info=1)
                        
        return {}, {}

    def atFrame(self, name, declarations):
        if declarations:            
            result = self.ruleset([self.selector('*')], declarations)
            # print "@BOX", name, declarations, result
            try:
                data = result[0]
                if data:
                    data = data.values()[0]
                    self.c.frameList.append(
                        self._pisaAddFrame(
                            name,
                            data))
            except Exception, e:
                log.warn(self.c.warning("@frame"), exc_info=1)            
        return {}, {}

class pisaCSSParser(css.CSSParser):

    def parseExternal(self, cssResourceName):
        
        # print "@import", self.rootPath, cssResourceName   
        oldRootPath = self.rootPath             
        cssFile = self.c.getFile(cssResourceName, relative=self.rootPath) # StringIO.StringIO("")
        result = []        
        if self.rootPath and self.rootPath.startswith("http:"):
            self.rootPath = urlparse.urljoin(self.rootPath, cssResourceName)
        else:
            self.rootPath = getDirName(cssFile)
        # print "###", self.rootPath
        if not cssFile:
            return None
        cssFile = file(cssFile, "r")
        result = self.parseFile(cssFile, True)
        self.rootPath = oldRootPath
        return result

class pisaContext:

    """
    Helper class for creation of reportlab story and container for 
    varoius data.    
    """

    def __init__(self, path, debug=0):
        self.fontList = copy.copy(pisa_default.DEFAULT_FONT)
        self.path = []
        self.node = None
        self.toc = PmlTableOfContents()
        self.story = []
        self.text = []
        self.log = []
        self.err = 0
        self.warn = 0      
        self.text = u""
        self.uidctr = 0
        self.multiBuild = False

        self.pageSize = A4
        self.template = None
        self.templateList = {}
        
        self.frameList = []
        self.frameStatic = {}
        self.frameStaticList = []
        self.pisaBackgroundList = []
        
        self.anchorFrag = []
        self.anchorName = []
        
        self.tableData = None
        
        self.frag = self.fragBlock = getParaFrag(ParagraphStyle('default%d' % self.UID()))
        self.fragList = []
        self.fragAnchor = []
        self.fragStack = []   
        self.fragStrip = True   
        
        self.listCounter = 0
        
        self.cssText = ""        
        
        self.pathCallback = None # External callback function for path calculations
        
        # Store path to document         
        self.pathDocument = path or "__dummy__"                 
        if not self.pathDocument.lower().startswith("http:"):
            self.pathDocument = os.path.abspath(self.pathDocument)
        self.pathDirectory = getDirName(self.pathDocument)        
        
        self.meta = dict(
            author = "",
            title = "",
            subject = "",
            keywords = "",
            pagesize = A4,
            )       

    def UID(self):
        self.uidctr += 1
        return self.uidctr

    # METHODS FOR CSS

    def addCSS(self, value):        
        value = value.strip()
        if value.startswith("<![CDATA["):
            value = value[9:-3]
        if value.startswith("<!--"):
            value = value[4:-3]
        self.cssText += value.strip() + "\n"

    def parseCSS(self):
        #print repr(self.cssText)
        
        # self.debug(9, self.cssText)
        
        # XXX Must be handled in a better way!
                
        #self.cssText = self.cssText.replace("<!--", "\n")
        #self.cssText = self.cssText.replace("-->", "\n")
        #self.cssText = self.cssText.replace("<![CDATA[", "\n")
        #self.cssText = self.cssText.replace("]]>", "\n")
        
        #self.debug(9, self.cssText)
           
        # print repr(self.cssText)
        # file("pisa.css", "wb").write(self.cssText.encode("utf8"))
        
        # self.cssText = re.compile(r"url\((.*?\))", re.M).sub('"\1"', self.cssText)
        # self.cssText = re.compile(r"\-moz\-.*?([\;\}]+)", re.M).sub(r"\1", self.cssText)

        # XXX Import has to be implemented!
        # self.cssText = re.compile(r"\@import.*;", re.M).sub("", self.cssText)

#        if 0:
#            try:
#                # Sanitize CSS
#                import cssutils
#                import logging            
#                cssutils.log.setlog(logging.getLogger('csslog'))
#                cssutils.log.setloglevel(logging.DEBUG)
#                sheet = cssutils.parseString(self.cssText)
#                self.cssText = sheet.cssText                
#                #err = csslog.getvalue()   
#            except ImportError, e:
#                pass     
#            except Exception, e:
#                log.exception(self.error("Error parsing CSS by cssutils"))
        
        # print self.cssText
        # file("pisa-sanitized.css", "w").write(self.cssText.encode("utf8"))        
        # print self.cssText
        
        
        self.cssBuilder = pisaCSSBuilder(mediumSet=["all", "print", "pdf"])        
        self.cssBuilder.c = self
        self.cssParser = pisaCSSParser(self.cssBuilder)   
        self.cssParser.rootPath = self.pathDirectory
        self.cssParser.c = self
        
        self.css = self.cssParser.parse(self.cssText)
        self.cssCascade = css.CSSCascadeStrategy(self.css)
        self.cssCascade.parser = self.cssParser

    # METHODS FOR STORY
    
    def addStory(self, data):        
        self.story.append(data)

    def swapStory(self, story=[]):
        self.story, story = copy.copy(story), copy.copy(self.story)
        return story

    def toParagraphStyle(self, first, full=False):
        style = ParagraphStyle('default%d' % self.UID(), keepWithNext=first.keepWithNext)
        style.fontName = first.fontName
        style.fontSize = first.fontSize
        style.leading = max(first.leading, first.fontSize * 1.25)
        style.backColor = first.backColor
        style.spaceBefore = first.spaceBefore
        style.spaceAfter = first.spaceAfter
        style.leftIndent = first.leftIndent
        style.rightIndent = first.rightIndent
        style.firstLineIndent = first.firstLineIndent
        style.textColor = first.textColor
        style.alignment = first.alignment
        style.bulletFontName = first.bulletFontName or first.fontName 
        style.bulletFontSize = first.fontSize
        style.bulletIndent = first.bulletIndent
        # Border handling for Paragraph
        style.borderWidth = 0
        if getBorderStyle(first.borderTopStyle):
            style.borderWidth = max(first.borderLeftWidth, first.borderRightWidth, first.borderTopWidth, first.borderBottomWidth)
            style.borderPadding = first.borderPadding # + first.borderWidth
            style.borderColor = first.borderTopColor
            # If no border color is given, the text color is used (XXX Tables!)
            if (style.borderColor is None) and style.borderWidth:
                style.borderColor = first.textColor      
        if full:
            style.fontName = tt2ps(first.fontName, first.bold, first.italic)
        return style       
    
    def addTOC(self):            
        # style = copy.deepcopy(self.toParagraphStyle(self.fragBlock))          
        #cssAttrs = copy.deepcopy(self.node.cssAttrs)
        frag = copy.deepcopy(self.frag)
        styles = [] 
        for i in range(0, 5):
            self.node.attributes["class"] = "pdftoclevel%d" % i    
            #self.node.cssAttrs = copy.deepcopy(cssAttrs)  
            self.frag = copy.deepcopy(frag)  
            self.cssAttr = pisa_parser.CSSCollect(self.node, self)            
            pisa_parser.CSS2Frag(self, {
                "margin-top": 0,
                "margin-bottom": 0,
                "margin-left": 0,
                "margin-right": 0,
                }, True)
            pstyle = self.toParagraphStyle(self.frag, True)            
            styles.append(copy.deepcopy(pstyle))
           
        # log.warn("%r", self.fragBlock.textColor)      
        self.toc.levelStyles = styles          
        self.addStory(self.toc)

    def addPara(self, force=False):
        
        # Cleanup the trail
        try:
            rfragList = reversed(self.fragList)
        except:            
            # For Python 2.3 compatibility
            rfragList = copy.copy(self.fragList)
            rfragList.reverse()
            
        for frag in rfragList:           
            frag.text = frag.text.rstrip()            
            if frag.text:        
                break
            
        if force or (self.text.strip() and self.fragList):
                    
            # Strip trailing whitespaces
            #for f in self.fragList:
            #    f.text = f.text.lstrip()
            #    if f.text: 
            #        break            
            #self.fragList[-1].lineBreak = self.fragList[-1].text.rstrip()  

            # Update paragraph style by style of first fragment
            first = self.fragBlock          
            style = self.toParagraphStyle(first)
                
            # borderRadius: None,
        
            # print repr(self.text.strip()), style.leading, "".join([repr(x.text) for x in self.fragList])

            # print first.leftIndent, first.listStyleType,repr(self.text) 
        
            bulletText = copy.copy(first.bulletText)
            first.bulletText = None
        
            # Add paragraph to story
            if force or len(self.fragAnchor + self.fragList)>0:
                para = PmlParagraph(
                    self.text,
                    style,
                    frags=self.fragAnchor + self.fragList,
                    bulletText=bulletText)
                
                # Mirrored and BIDI
                #import unicodedata
                #for c in self.text:                
                #    print unicodedata.bidirectional(c), 
                
                # XXX ???    
                # print repr(para)
                            
                para.outline = first.outline
                para.outlineLevel = first.outlineLevel
                para.outlineOpen = first.outlineOpen
                
                self.addStory(para)
            
            self.fragAnchor = []
            first.bulletText = None
            
        self.clearFrag()

    # METHODS FOR FRAG

    def clearFrag(self):
        self.fragList = []
        self.fragStrip = True
        self.text = u""

    def copyFrag(self, **kw):
        frag = copy.deepcopy(self.frag)
        for k, v in kw.items():
            setattr(frag, k, v) 
        return frag

    def newFrag(self, **kw):
        self.frag = copy.deepcopy(self.frag)
        for k, v in kw.items():
            setattr(self.frag, k, v) 
        return self.frag

    def _appendFrag(self, frag):
        if frag.link and frag.link.startswith("#"):
            self.anchorFrag.append((frag, frag.link[1:]))
        self.fragList.append(frag)

    def addFrag(self, text="", frag=None):     
        
        frag = baseFrag = copy.deepcopy(self.frag)
        
        # if sub and super are both on they will cancel each other out
        if frag.sub == 1 and frag.super == 1:
            frag.sub = 0
            frag.super = 0

        # XXX Has to be replaced by CSS styles like vertical-align and font-size
        if frag.sub:
            frag.rise = -frag.fontSize * subFraction
            frag.fontSize = max(frag.fontSize-sizeDelta, 3)
        elif frag.super:
            frag.rise = frag.fontSize * superFraction
            frag.fontSize = max(frag.fontSize-sizeDelta, 3)

        if frag.greek:
            frag.fontName = 'symbol'
            data = _greekConvert(data)

        # bold, italic, and underline
        frag.fontName = frag.bulletFontName = tt2ps(frag.fontName, frag.bold, frag.italic)
        # print frag.bulletFontName

        # Modify text for optimal whitespace handling
        # XXX Support Unicode whitespaces?
        # XXX What about images?
        
        # XXX Doesn't work with Reportlab > 2.1
        # NBSP = '\xc2\xa0' # u"_"
        NBSP = u"\u00a0"
        
        # Replace &shy; with empty and normalize NBSP
        text = (text
            .replace(u"\xad", u"")
            .replace(u"\xc2\xa0", NBSP)
            .replace(u"\xa0", NBSP)) 
        
        # log.debug("> %r", text)
        
        if frag.whiteSpace == "pre":     
            
            # Handle by lines       
            for text in re.split(r'(\r\n|\n|\r)', text):                
                self.text += text                
                if ("\n" in text) or ("\r" in text):
                    # If EOL insert a linebreak
                    frag = copy.deepcopy(baseFrag)
                    frag.text = ""
                    frag.lineBreak = 1
                    self._appendFrag(frag) 
                else:
                    # Handle tabs in a simple way
                    text = text.replace(u"\t", 8 * u" ")                    
                    # Somehow for Reportlab NBSP have to be inserted 
                    # as single character fragments
                    for text in re.split(r'(\ )', text):  
                        frag = copy.deepcopy(baseFrag)
                        if text == " ":
                            text = NBSP 
                        frag.text = text
                        self._appendFrag(frag)                
        else: 
            for text in re.split(u'(' + NBSP + u')', text):   
                frag = copy.deepcopy(baseFrag)               
                if text == NBSP:                    
                    frag.text = NBSP
                    self.text += text
                    self._appendFrag(frag)
                else:                    
                    frag.text = " ".join(("x" + text + "x").split())[1:-1]       
                    if self.fragStrip:
                        frag.text = frag.text.lstrip()
                        if frag.text:
                            self.fragStrip = False            
                    self.text += frag.text
                    self._appendFrag(frag)
        # print frag.fontName, repr(frag.text), frag.bulletText                   
    
    def pushFrag(self):
        self.fragStack.append(self.frag)
        self.newFrag()

    def pullFrag(self):
        self.frag = self.fragStack.pop()
    
    # XXX
                            
    def _getFragment(self, l=20):
        try:
            return repr(" ".join(self.node.toxml().split()[:l]))
        except:
            return ""

    def _getLineNumber(self):
        return 0

    def context(self, msg):
        return "%s\n%s" % (
                str(msg),
                self._getFragment(50))
#        return "line %s: %s\n%s" % (                
#                self._getLineNumber(), 
#                str(msg), 
#                self._getFragment(50))

    def warning(self, msg, *args):
        self.warn += 1
        self.log.append((pisa_default.PML_WARNING, self._getLineNumber(), str(msg), self._getFragment(50)))
        return self.context(msg % args)

    def error(self, msg, *args):
        self.err += 1                
        self.log.append((pisa_default.PML_ERROR, self._getLineNumber(), str(msg), self._getFragment(50)))
        return self.context(msg % args)
    
    # UTILS
    
    def getFile(self, name, relative=None):
        """
        Returns a file name or None
        """
        try:
            path = relative or self.pathDirectory
            if self.pathCallback is not None:
                nv = self.pathCallback(name, relative)
            else:                
                if path is None:
                    log.warn("Could not find main directory for getting filename. Use CWD")
                    path = os.getcwd()
                nv = os.path.normpath(os.path.join(path, name))                            
                if not(nv and os.path.isfile(nv)):
                    nv = None
            if nv is None:
                log.warn(self.warning("File '%s' does not exist" % (name)))
            return nv
        except:
            log.warn(self.warning("getFile %r %r %r", name, relative, path), exc_info=1)
            
    def getFontName(self, names, default="helvetica"):
        """
        Name of a font
        """
        # print names, self.fontList
        if type(names) is not types.ListType: 
            names = str(names).strip().split(",")
        for name in names:
            font = self.fontList.get(str(name).strip().lower(), None)
            if font is not None:
                return font
        return self.fontList.get(default, None)

    def registerFont(self, fontname, alias=[]):
        self.fontList[str(fontname).lower()] = str(fontname)
        for a in alias:
            self.fontList[str(a)] = str(fontname)
            
    def loadFont(self, names, src, encoding="WinAnsiEncoding", bold=0, italic=0):
        
        if names and src:
            if type(names) is types.ListType:
                fontAlias = names
            else:
                fontAlias = [x.lower().strip() for x in names.split(",") if x]
            
            # XXX Problems with unicode here 
            fontAlias = [str(x) for x in fontAlias]
            src = str(src)
            
            fontName = fontAlias[0]
            parts = src.split(".")                
            baseName, suffix = ".".join(parts[:-1]), parts[-1]
            suffix = suffix.lower()
                        
            try:
                
                if suffix == "ttf":

                    # determine full font name according to weight and style
                    fullFontName = "%s_%d%d" % (fontName, bold, italic)                    

                    # check if font has already been registered
                    if fullFontName in self.fontList:
                        log.warn(self.warning("Repeated font embed for %s, skip new embed " % fullFontName))
                    else:
                                                
                        # Register TTF font and special name 
                        pdfmetrics.registerFont(TTFont(fullFontName, src))
                        
                        # Add or replace missing styles
                        for bold in (0, 1):
                            for italic in (0, 1):                                                                
                                if ("%s_%d%d" % (fontName, bold, italic)) not in self.fontList:
                                    addMapping(fontName, bold, italic, fullFontName)

                        # Register "normal" name and the place holder for style                                                
                        self.registerFont(fontName, fontAlias + [fullFontName])
                                         
                elif suffix in ("afm", "pfb"):
                    
                    afm = baseName + ".afm"
                    pfb = baseName + ".pfb"

                    # determine full font name according to weight and style
                    fullFontName = "%s_%d%d" % (fontName, bold, italic)   
                        
                    #fontNameOriginal = ""
                    #for line in open(afm).readlines()[:-1]:
                    #    if line[:16] == 'StartCharMetrics':
                    #        self.error("Font name not found")
                    #    if line[:8] == 'FontName':
                    #        fontNameOriginal = line[9:].strip()
                    #        break
                                   
                    # check if font has already been registered
                    if fullFontName in self.fontList:
                        log.warn(self.warning("Repeated font embed for %s, skip new embed" % fontName))
                    else:                                              
                        
                        # Include font                 
                        face = pdfmetrics.EmbeddedType1Face(afm, pfb)                        
                        fontNameOriginal = face.name
                        pdfmetrics.registerTypeFace(face)
                        # print fontName, fontNameOriginal, fullFontName
                        justFont = pdfmetrics.Font(fullFontName, fontNameOriginal, encoding)
                        pdfmetrics.registerFont(justFont)
                        
                         # Add or replace missing styles
                        for bold in (0, 1):
                            for italic in (0, 1):                                                                
                                if ("%s_%d%d" % (fontName, bold, italic)) not in self.fontList:
                                    addMapping(fontName, bold, italic, fontNameOriginal)
                        
                        # Register "normal" name and the place holder for style                                                
                        self.registerFont(fontName, fontAlias + [fullFontName, fontNameOriginal])
    
                        #import pprint
                        #pprint.pprint(self.fontList)
    
                else:
                    log.warning(self.warning("wrong attributes for <pdf:font>"))
    
            except Exception, e:
                log.warn(self.warning("Loading font '%s'", fontName), exc_info=1)                
