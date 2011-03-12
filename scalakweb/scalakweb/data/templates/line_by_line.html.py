from mako import runtime, filters, cache
UNDEFINED = runtime.UNDEFINED
__M_dict_builtin = dict
__M_locals_builtin = locals
_magic_number = 5
_modified_time = 1292769285.660363
_template_filename='/usr/local/lib/python2.6/dist-packages/ScalakWeb-0.1dev-py2.6.egg/scalakweb/templates/line_by_line.html'
_template_uri='/line_by_line.html'
_template_cache=cache.Cache(__name__, _modified_time)
_source_encoding='utf-8'
from webhelpers.html import escape
_exports = []


def render_body(context,**pageargs):
    context.caller_stack._push_frame()
    try:
        __M_locals = __M_dict_builtin(pageargs=pageargs)
        c = context.get('c', UNDEFINED)
        __M_writer = context.writer()
        # SOURCE LINE 1
        for key, value in c.lineData:
            # SOURCE LINE 2
            __M_writer(u'<div style="display:block;"> <b>')
            __M_writer(escape(key))
            __M_writer(u'</b>: ')
            __M_writer(escape(value))
            __M_writer(u' </div>\n')
        return ''
    finally:
        context.caller_stack._pop_frame()


