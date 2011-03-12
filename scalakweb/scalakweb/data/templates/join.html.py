from mako import runtime, filters, cache
UNDEFINED = runtime.UNDEFINED
__M_dict_builtin = dict
__M_locals_builtin = locals
_magic_number = 5
_modified_time = 1292769281.026686
_template_filename='/usr/local/lib/python2.6/dist-packages/ScalakWeb-0.1dev-py2.6.egg/scalakweb/templates/join.html'
_template_uri='/join.html'
_template_cache=cache.Cache(__name__, _modified_time)
_source_encoding='utf-8'
from webhelpers.html import escape
_exports = []


def render_body(context,**pageargs):
    context.caller_stack._push_frame()
    try:
        __M_locals = __M_dict_builtin(pageargs=pageargs)
        h = context.get('h', UNDEFINED)
        __M_writer = context.writer()
        # SOURCE LINE 1
        __M_writer(u'<h4>Enter project ID (note that Your request must be accepted by project administrator)</h4>\n\n')
        # SOURCE LINE 3
        __M_writer(escape(h.form(h.url(controller='scalak_user', action='joinSubmit'), method='post')))
        __M_writer(u'\nProject id: ')
        # SOURCE LINE 4
        __M_writer(escape(h.text('project_id')))
        __M_writer(u'\n               ')
        # SOURCE LINE 5
        __M_writer(escape(h.submit('submit', 'Send request')))
        __M_writer(u'\n')
        # SOURCE LINE 6
        __M_writer(escape(h.end_form()))
        __M_writer(u'\n')
        return ''
    finally:
        context.caller_stack._pop_frame()


