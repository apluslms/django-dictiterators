from django.template.defaulttags import ForNode
from django.template import Node, NodeList, Library


register = Library()


class DictUnpackNode(Node):
    CONTEXT_VAR = '__dict__'

    def __init__(self, nodelist):
        self.nodelist = nodelist

    def __repr__(self):
        return "<DictUnpackNode>"

    def render(self, context):
        values = context[self.CONTEXT_VAR]
        with context.push(**values):
            return self.nodelist.render(context)


@register.tag
def foreachdict(parser, token):
    bits = token.split_contents()
    if len(bits) < 2:
        raise TemplateSyntaxError("'foreachdict' statements should have at least two"
                                  " words: %s" % token.contents)

    is_reversed = bits[-1] == 'reversed'
    sequence_i = 2 if bits[1] == 'in' else 1
    if len(bits) < sequence_i:
        raise TemplateSyntaxError("'foreachdict' statements is missing squence: "
                                  "%s" % token.contents)

    sequence = parser.compile_filter(bits[sequence_i])
    loopvars = [DictUnpackNode.CONTEXT_VAR]
    nodelist_loop = parser.parse(('empty', 'endforeachdict',))
    nodelist_loop = NodeList(DictUnpackNode(nodelist_loop))
    token = parser.next_token()
    if token.contents == 'empty':
        nodelist_empty = parser.parse(('endforeachdict',))
        parser.delete_first_token()
    else:
        nodelist_empty = None
    return ForNode(loopvars, sequence, is_reversed, nodelist_loop, nodelist_empty)
