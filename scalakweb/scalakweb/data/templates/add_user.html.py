from mako import runtime, filters, cache
UNDEFINED = runtime.UNDEFINED
__M_dict_builtin = dict
__M_locals_builtin = locals
_magic_number = 5
_modified_time = 1292763451.0576799
_template_filename='/usr/local/lib/python2.6/dist-packages/ScalakWeb-0.1dev-py2.6.egg/scalakweb/templates/add_user.html'
_template_uri='/add_user.html'
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
        __M_writer(u'<h3>Enter user login (note that user must exists in Scalak)</h3>\n\n')
        # SOURCE LINE 3
        __M_writer(escape(h.form(h.url(controller='project', action='userAddSubmit'), method='post')))
        __M_writer(u'\nUser login: ')
        # SOURCE LINE 4
        __M_writer(escape(h.text('user_login')))
        __M_writer(u'\n               ')
        # SOURCE LINE 5
        __M_writer(escape(h.submit('submit', 'Submit')))
        __M_writer(u'\n')
        # SOURCE LINE 6
        __M_writer(escape(h.end_form()))
        __M_writer(u'\n')
        return ''
    finally:
        context.caller_stack._pop_frame()


