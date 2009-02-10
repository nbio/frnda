# -*- coding: ISO-8859-1 -*-
#############################################
## (C)opyright by Dirk Holtwick, 2002-2007 ##
## All rights reserved                     ##
#############################################

__reversion__ = "$Revision: 20 $"
__author__    = "$Author: holtwick $"
__date__      = "$Date: 2007-10-09 12:58:24 +0200 (Di, 09 Okt 2007) $"

from pisa_context import pisaContext
from pisa_parser import pisaParser
from pisa_util import *
from pisa_reportlab import *
from pisa_default import DEFAULT_CSS

import os
import types
import cgi

def pisaErrorDocument(dest, c):
    out = StringIO.StringIO()
    out.write("<p style='background-color:red;'><strong>%d error(s) occured:</strong><p>" % c.err)
    for mode, line, msg, code in c.log:
        if mode=="error":
            out.write("<pre>%s in line %d: %s</pre>" % (mode, line, cgi.escape(msg)))

    out.write("<p><strong>%d warning(s) occured:</strong><p>" % c.warn)
    for mode, line, msg, code in c.log:
        if mode=="warning":
            out.write("<p>%s in line %d: %s</p>" % (mode, line, cgi.escape(msg)))

    return pisaDocument(out.getvalue(), dest)

def pisaStory(
    src,
    path = None,
    link_callback = None,
    debug = 0,
    default_css = None,
    xhtml = False,
    encoding = None,
    **kw):
    
    # Prepare Context
    c = pisaContext(path, debug=debug)
    c.pathCallback = link_callback

    # Use a default set of CSS definitions to get an expected output
    if default_css is None:
        default_css = DEFAULT_CSS
    
    # Parse and fill the story    
    pisaParser(src, c, default_css, xhtml, encoding)

    #if 0:
    #    import reportlab.pdfbase.pdfmetrics as pm
    #    pm.dumpFontData()
    
    # Avoid empty documents
    if not c.story:
        c.addPara(force=True)
    
    # Remove anchors if they do not exist (because of a bug in Reportlab)    
    for frag, anchor in c.anchorFrag:
        if anchor not in c.anchorName:
            frag.link = None
            
    return c

def pisaDocument(
    src,
    dest,
    path = None,
    link_callback = None,
    debug = 0,
    show_error_as_pdf = False,
    default_css = None,
    xhtml = False,
    encoding = None,
    **kw):

    try:

        log.debug("pisaDocument options:\n  src = %r\n  dest = %s\n  path = %r\n  link_callback = %r\n  xhtml = %r",
            src,
            dest,
            path,
            link_callback,
            xhtml)

        c = pisaStory(src, path, link_callback, debug, default_css, xhtml, encoding)

        # Buffer PDF into memory
        out = StringIO.StringIO()

        doc = PmlBaseDoc(
            out,
            pagesize = c.pageSize,
            author = c.meta["author"].strip(),
            subject = c.meta["subject"].strip(),
            keywords = [x.strip() for x in c.meta["keywords"].strip().split(",") if x],
            title = c.meta["title"].strip(),
            showBoundary = 0,
            allowSplitting = 1)

        # XXX It is not possible to access PDF info, because it is private in canvas
        # doc.info.producer = "pisa <http://www.holtwick.it>"

        # Prepare templates and their frames
        if c.templateList.has_key("body"):
            body = c.templateList["body"]
            del c.templateList["body"]
        else:
            x, y, w, h = getBox("1cm 1cm -1cm -1cm", c.pageSize)
            body = PmlPageTemplate(
                id="body",
                frames=[
                    Frame(x, y, w, h,
                        id = "body",
                        leftPadding = 0,
                        rightPadding = 0,
                        bottomPadding = 0,
                        topPadding = 0)],
                pagesize = c.pageSize)

        # print body.frames

        # print [body] + c.templateList.values()
        doc.addPageTemplates([body] + c.templateList.values())

        # Use multibuild e.g. if a TOC has to be created
        if c.multiBuild:
            doc.multiBuild(c.story)
        else:
            doc.build(c.story)

        # Add watermarks
        if pyPdf:
            # print c.pisaBackgroundList
            for bgouter in c.pisaBackgroundList:
                # If we have at least one background, then lets do it
                if bgouter:
                    istream = out
                    # istream.seek(2,0) #StringIO.StringIO(data)
                    try:
                        output = pyPdf.PdfFileWriter()
                        input1 = pyPdf.PdfFileReader(istream)
                        ctr = 0
                        for bg in c.pisaBackgroundList:
                            page = input1.getPage(ctr)
                            if bg:
                                if os.path.exists(bg):
                                    # print "BACK", bg
                                    bginput = pyPdf.PdfFileReader(open(bg, "rb"))
                                    # page.mergePage(bginput.getPage(0))
                                    pagebg = bginput.getPage(0)
                                    pagebg.mergePage(page)
                                    page = pagebg
                                else:
                                    log.warn(c.warning("Background PDF %s doesn't exist." % bg))
                            output.addPage(page)
                            ctr += 1
                        out = StringIO.StringIO()
                        output.write(out)
                        # data = sout.getvalue()
                    except Exception:
                        log.exception(c.error("pyPDF error"))
                    # istream.close()
                # Found a background? So leave loop after first occurence
                break
        else:
            log.warn(c.warning("pyPDF not installed!"))

        # Get the resulting PDF and write it to the file object
        # passed from the caller
        data = out.getvalue()
        dest.write(data)

    except:
        # log.exception(c.error("Document error"))
        log.exception("Document error")

    # In web frameworks for debugging purposes maybe an output of
    # errors in a PDF is preferred
    if c.err and show_error_as_pdf:
        return pisaErrorDocument(dest, c)

    return c
