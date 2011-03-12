from mako import runtime, filters, cache
UNDEFINED = runtime.UNDEFINED
__M_dict_builtin = dict
__M_locals_builtin = locals
_magic_number = 5
_modified_time = 1292763437.548727
_template_filename='/usr/local/lib/python2.6/dist-packages/ScalakWeb-0.1dev-py2.6.egg/scalakweb/templates/edit_project.html'
_template_uri='/edit_project.html'
_template_cache=cache.Cache(__name__, _modified_time)
_source_encoding='utf-8'
from webhelpers.html import escape
_exports = []


def render_body(context,**pageargs):
    context.caller_stack._push_frame()
    try:
        __M_locals = __M_dict_builtin(pageargs=pageargs)
        h = context.get('h', UNDEFINED)
        c = context.get('c', UNDEFINED)
        __M_writer = context.writer()
        # SOURCE LINE 1
        __M_writer(u'\n')
        # SOURCE LINE 2
        __M_writer(escape(h.form(h.url(controller='project', action='projectInfoEditSubmit'), method='post')))
        __M_writer(u'\n<table>\n    <tbody>\n        <tr>\n            <td>Id:</td>\n            <td>')
        # SOURCE LINE 7
        __M_writer(escape(c.name))
        __M_writer(u'</td>\n        </tr>\n        <tr>\n            <td>Administrator:</td>\n            <td>')
        # SOURCE LINE 11
        __M_writer(escape(c.admin))
        __M_writer(u'</td>\n        </tr>\n        <tr>\n            <td>Creation date:</td>\n            <td>')
        # SOURCE LINE 15
        __M_writer(escape(c.create_date))
        __M_writer(u'</td>\n        </tr>\n        <tr>\n            <td>Due date:</td>\n            <td>')
        # SOURCE LINE 19
        __M_writer(escape(c.due_date))
        __M_writer(u'</td>\n        </tr>\n        <tr>\n            <td>Brief description:</td>\n            <td>')
        # SOURCE LINE 23
        __M_writer(escape(h.text('brief', c.brief, size=30, maxlength=50)))
        __M_writer(u'</td>\n        </tr>\n        <tr>\n            <td>Full description:</td>\n            <td>')
        # SOURCE LINE 27
        __M_writer(escape(h.textarea('description', c.description, cols=30, rows=10)))
        __M_writer(u'</td>\n        </tr>\n    </tbody>\n</table>\n')
        # SOURCE LINE 31
        __M_writer(escape(h.submit('submit', 'Submit')))
        __M_writer(u'\n')
        # SOURCE LINE 32
        __M_writer(escape(h.end_form()))
        __M_writer(u'\n')
        return ''
    finally:
        context.caller_stack._pop_frame()


