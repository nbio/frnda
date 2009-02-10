from django.conf import settings
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.http import HttpResponse
import datetime
import cStringIO as StringIO

import sys
sys.path = ["reportlab/lib",] + sys.path
sys.path = ["pisa",] + sys.path

from ho.pisa import pisaDocument


def home(request, **kwargs):
    is_form = True
    is_home = True
    return render_to_response('pages/home.html', locals(), context_instance=RequestContext(request))


def pdf(request, **kwargs):
    html = """<html>
<head><style type="text/css">
	@page {
		size: a4;
		margin: 1cm;
		@frame footer {
    		-pdf-frame-content: footerContent;
    		bottom: 1cm;
    		margin-left: 1cm;
    		margin-right: 1cm;
    		height: 1cm;
		}
	}
</style>
</head>
<body><h1>YO MAMA</h1></body>
</html>"""
    result = StringIO.StringIO()
    pdf = pisaDocument(StringIO.StringIO(html.encode("UTF-8")), result)
    if not pdf.err:
        return HttpResponse(result.getvalue(), mimetype='application/pdf')
    return HttpResponse('We had some errors<pre>%s</pre>' % cgi.escape(html))
