# -*- coding: ISO-8859-1 -*-
#############################################
## (C)opyright by Dirk Holtwick, 2002-2007 ##
## All rights reserved                     ##
#############################################

__reversion__ = "$Revision: 20 $"
__author__    = "$Author: holtwick $"
__date__      = "$Date: 2007-10-09 12:58:24 +0200 (Di, 09 Okt 2007) $"

from pisa_util import *
from pisa_default import TAGS, STRING
# from reportlab.platypus.paragraph import *
import copy
import cgi

class PmlBaseDoc(BaseDocTemplate):

    """
    We use our own document template to get access to the canvas
    and set some informations once.
    """

    def beforePage(self):

        # Tricky way to set producer, because of not real privateness in Python
        self.canv._doc.info.producer = "pisa HTML to PDF <http://www.htmltopdf.org>"

        '''
        # Convert to ASCII because there is a Bug in Reportlab not
        # supporting other than ASCII. Send to list on 23.1.2007

        author = toString(self.pml_data.get("author", "")).encode("ascii","ignore")
        subject = toString(self.pml_data.get("subject", "")).encode("ascii","ignore")
        title = toString(self.pml_data.get("title", "")).encode("ascii","ignore")
        # print repr((author,title,subject))

        self.canv.setAuthor(author)
        self.canv.setSubject(subject)
        self.canv.setTitle(title)

        if self.pml_data.get("fullscreen", 0):
            self.canv.showFullScreen0()

        if self.pml_data.get("showoutline", 0):
            self.canv.showOutline()

        if self.pml_data.get("duration", None) is not None:
            self.canv.setPageDuration(self.pml_data["duration"])
        '''

    def afterFlowable(self, flowable):
        # Does the flowable contain fragments?
        if getattr(flowable, "outline", False):
            self.notify('TOCEntry', (
                flowable.outlineLevel,
                cgi.escape(copy.deepcopy(flowable.text), 1),
                self.page))

class PmlPageTemplate(PageTemplate):

    def __init__(self, **kw):
        self.pisaStaticList = []
        self.pisaBackgroundList = []
        self.pisaBackground = None
        PageTemplate.__init__(self, **kw)

    def beforeDrawPage(self, canvas, doc):
        canvas.saveState()
        try:

            try:
                # Paint static frames
                pagenumber = str(canvas.getPageNumber())
                for frame in self.pisaStaticList:

                    frame = copy.deepcopy(frame)
                    story = frame.pisaStaticStory

                    # Modify page number
                    for obj in story:
                        if isinstance(obj, PmlParagraph):
                            for frag in obj.frags:
                                if frag.pageNumber:
                                    frag.text = pagenumber

                    frame.addFromList(story, canvas)

            except Exception, e:
                log.debug("PmlPageTemplate", exc_info=1)

            try:
                self.pisaBackgroundList.append(self.pisaBackground)
            except:
                self.pisaBackgroundList.append(None)

            # canvas.saveState()
            #try:
            #    self.pml_drawing.draw(canvas)
            #except Exception, e:
            #    # print "drawing exception", str(e)
            #    pass
        finally:
            canvas.restoreState()

class PmlImage(Image):

    def wrap(self, availWidth, availHeight):
        #print 123, self.drawWidth, self.drawHeight, self.pisaZoom
        #self.drawWidth *= self.pisaZoom
        #self.drawHeight *= self.pisaZoom
        # print 456, self.drawWidth, self.drawHeight
        width = min(self.drawWidth, availWidth)
        # print 999, width, self.drawWidth, availWidth
        factor = float(width) / self.drawWidth
        # print 123, factor
        self.drawHeight = self.drawHeight * factor
        self.drawWidth = width
        return Image.wrap(self, availWidth, availHeight)

class PmlParagraph(Paragraph):

    def draw(self):

        # Insert page number
        '''
        if 0: #for line in self.blPara.lines:
            try:
                for frag in line.words:
                    #print 111,frag.pageNumber, frag.text
                    if frag.pageNumber:
                        frag.text = str(self.canv.getPageNumber())
            except Exception, e:
                log.debug("PmlParagraph", exc_info=1)
        '''

        # Create outline
        if getattr(self, "outline", False):

            # Check level and add all levels
            last = getattr(self.canv, "outlineLast", -1) + 1
            while last < self.outlineLevel:
                # print "(OUTLINE",  last, self.text
                key = getUID()
                self.canv.bookmarkPage(key)
                self.canv.addOutlineEntry(
                    copy.deepcopy(self.text),
                    key,
                    last,
                    not self.outlineOpen)
                last += 1
            self.canv.outlineLast = self.outlineLevel

            key = getUID()
            # print " OUTLINE", self.outlineLevel, self.text
            self.canv.bookmarkPage(key)
            self.canv.addOutlineEntry(
                copy.deepcopy(self.text),
                key,
                self.outlineLevel,
                not self.outlineOpen)
            last += 1

        #else:
        #    print repr(self.text)[:80]

        # Usual stuff
        Paragraph.draw(self)

class PmlTableOfContents(TableOfContents):

    def wrap(self, availWidth, availHeight):
        "All table properties should be known by now."

        widths = (availWidth - self.rightColumnWidth,
                  self.rightColumnWidth)

        # makes an internal table which does all the work.
        # we draw the LAST RUN's entries!  If there are
        # none, we make some dummy data to keep the table
        # from complaining
        if len(self._lastEntries) == 0:
            _tempEntries = [(0,'Placeholder for table of contents',0)]
        else:
            _tempEntries = self._lastEntries

        i = 0
        lastMargin = 0
        tableData = []
        tableStyle = [
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
            ]
        for (level, text, pageNum) in _tempEntries:
            leftColStyle = self.levelStyles[level]
            if i: # Not for first element
                tableStyle.append((
                    'TOPPADDING',
                    (0,i), (-1, i),
                    max(lastMargin, leftColStyle.spaceBefore)))
            # print leftColStyle.leftIndent
            lastMargin = leftColStyle.spaceAfter
            #right col style is right aligned
            rightColStyle = ParagraphStyle(name='leftColLevel%d' % level,
                                           parent=leftColStyle,
                                           leftIndent=0,
                                           alignment=TA_RIGHT)
            leftPara = Paragraph(text, leftColStyle)
            rightPara = Paragraph(str(pageNum), rightColStyle)
            tableData.append([leftPara, rightPara])
            i += 1

        self._table = Table(
            tableData,
            colWidths=widths,
            style=TableStyle(tableStyle))

        self.width, self.height = self._table.wrapOn(self.canv,availWidth, availHeight)
        return (self.width, self.height)

class PmlRightPageBreak(CondPageBreak):

    def __init__(self):
        pass

    def wrap(self, availWidth, availHeight):
        if (0==(self.canv.getPageNumber()%2)):
            self.width = availWidth
            self.height = availHeight
            return (availWidth,availHeight)
        self.width = 0
        self.height = 0
        return (0,0)

class PmlLeftPageBreak(CondPageBreak):

    def __init__(self):
        pass

    def wrap(self, availWidth, availHeight):
        if (1==(self.canv.getPageNumber()%2)):
            self.width = availWidth
            self.height = availHeight
            return (availWidth,availHeight)
        self.width = 0
        self.height = 0
        return (0,0)

