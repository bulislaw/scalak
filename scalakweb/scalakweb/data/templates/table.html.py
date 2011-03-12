from mako import runtime, filters, cache
UNDEFINED = runtime.UNDEFINED
__M_dict_builtin = dict
__M_locals_builtin = locals
_magic_number = 5
_modified_time = 1292769280.1369159
_template_filename='/usr/local/lib/python2.6/dist-packages/ScalakWeb-0.1dev-py2.6.egg/scalakweb/templates/table.html'
_template_uri='/table.html'
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
        __M_writer(u'<table style="')
        __M_writer(escape(c.style or ""))
        __M_writer(u'">\n    <thead>\n        <tr>\n')
        # SOURCE LINE 4
        for h in c.header:
            # SOURCE LINE 5
            __M_writer(u'                <th style="padding: 10px" scope="col">')
            __M_writer(escape(h))
            __M_writer(u'</th>\n')
        # SOURCE LINE 7
        __M_writer(u'        </tr>\n    </thead>\n    <tbody>\n')
        # SOURCE LINE 10
        for row in c.rows:
            # SOURCE LINE 11
            __M_writer(u'            <tr>\n')
            # SOURCE LINE 12
            for col in row:
                # SOURCE LINE 13
                __M_writer(u'                    <td>')
                __M_writer(escape(col))
                __M_writer(u'</td>\n')
            # SOURCE LINE 15
            __M_writer(u'            </tr>\n')
        # SOURCE LINE 17
        __M_writer(u'    </tbody>\n</table>\n')
        return ''
    finally:
        context.caller_stack._pop_frame()


