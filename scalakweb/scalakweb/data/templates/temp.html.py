from mako import runtime, filters, cache
UNDEFINED = runtime.UNDEFINED
__M_dict_builtin = dict
__M_locals_builtin = locals
_magic_number = 5
_modified_time = 1292769280.150568
_template_filename='/usr/local/lib/python2.6/dist-packages/ScalakWeb-0.1dev-py2.6.egg/scalakweb/templates/temp.html'
_template_uri='/temp.html'
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
        __M_writer(u'<html>\n<head>\n    <style type="text/css">\n        h1, p, body, html, div {margin:0;padding:0}\n        \n        a:link {color: #000000; text-decoration: underline; }\n        a:active {color: #8b0304; text-decoration: underline; }\n        a:visited {color: #000000; text-decoration: underline; }\n        a:hover {color: #8b0304; text-decoration: none; }\n\n        body {\n            background: #E8E8E8;\n        }\n\n        ul {\n            font-size: 13px; \n        }\n\n        div.header {\n            width: 100%;\n            height: 60px;\n            padding-left: 15%;\n            padding-top: 15px;\n            background: #E8E8E8;\n            border-bottom: 5px #8b0304  solid; \n            float: left;\n        }   \n\n        div.logo {\n            border-right: 2px black solid;\n            float: left;\n            position: inline;\n            padding-right: 15px;\n            margin-right: 20px;\n        }\n\n        div.title {\n            float: left;\n            position: inline;\n        }\n\n        div.menu {\n            width: 15%;\n            background: #E8E8E8;\n            padding-top: 25px;\n            padding-bottom: 25px;\n            padding-left: 3%;\n            padding-right: 2%;\n            text-align: left;\n            float: left;\n            display: inline;\n        }   \n\n        div.main {\n            <!--height: 30%;-->\n            background: white;\n            border: 2px #8b0304 solid;\n            padding: 25px;\n            margin-top: 30px;\n            display: block;\n        }\n\n        div.footer {\n            text-align: right;\n            font-size: 9px;\n            font-color: silver;\n            display: block;\n            padding-top: 10px;\n            padding-right: 15px;\n        }\n\n        ul#flash-messages {\n            font-style: italic;\n            padding: 4px;\n            padding-left: 40px;\n            list-style: none;\n            border: 2px black solid;\n        }\n\n        div.center {\n            width: 70%;\n            margin-left: 20px;\n            float: left;\n            display: inline;\n        }\n\n        .red {\n            color: #8b0304;\n        }\n\n        .underline {\n            text-decoration: underline;\n        }\n\n    </style>\n    <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />\n</head>\n<body>\n    <div class="header"> \n        <div class="logo"><h1>Scalak</h1></div>\n        <div class="title"><h3>')
        # SOURCE LINE 101
        __M_writer(escape(c.site))
        __M_writer(u'</h3></div>\n    </div>\n    <div class="menu">\n        <h4 class="red">')
        # SOURCE LINE 104
        __M_writer(escape(c.name))
        __M_writer(u'</h4>\n        <ul class="menu">\n')
        # SOURCE LINE 106
        for top_item in c.menu:
            # SOURCE LINE 107
            __M_writer(u'                <li><a href="')
            __M_writer(escape(top_item.link))
            __M_writer(u'">')
            __M_writer(escape(top_item.name))
            __M_writer(u'</a>\n')
            # SOURCE LINE 108
            if top_item.getMenu():
                # SOURCE LINE 109
                __M_writer(u'                    <ul>\n')
                # SOURCE LINE 110
                for item in top_item.getMenu():
                    # SOURCE LINE 111
                    __M_writer(u'                        <li><a href="')
                    __M_writer(escape(item.link))
                    __M_writer(u'">')
                    __M_writer(escape(item.name))
                    __M_writer(u'</a>\n')
                # SOURCE LINE 113
                __M_writer(u'                    </ul>\n')
        # SOURCE LINE 116
        __M_writer(u'        </ul>\n    </div>\n    <div class="center">\n        ')
        # SOURCE LINE 119
        messages = h.flash.pop_messages() 
        
        __M_locals.update(__M_dict_builtin([(__M_key, __M_locals_builtin()[__M_key]) for __M_key in ['messages'] if __M_key in __M_locals_builtin()]))
        __M_writer(u'\n')
        # SOURCE LINE 120
        if messages:
            # SOURCE LINE 121
            __M_writer(u'        <ul id="flash-messages">\n')
            # SOURCE LINE 122
            for message in messages:
                # SOURCE LINE 123
                __M_writer(u'            <li>')
                __M_writer(escape(message))
                __M_writer(u'</li>\n')
            # SOURCE LINE 125
            __M_writer(u'        </ul>\n')
        # SOURCE LINE 127
        __M_writer(u'        <div class="main">\n            ')
        # SOURCE LINE 128
        __M_writer(escape(c.content))
        __M_writer(u'\n        </div>\n\n        <div class="footer">\n            Powered by Scalak Copyright 2010 Bartosz Szatkowski\n        </div>\n    </div>\n</body>\n</html>\n')
        return ''
    finally:
        context.caller_stack._pop_frame()


