from django.template import Node, NodeList, Library
from django.template.defaulttags import ForNode
from django.utils.safestring import mark_safe


register = Library()


class ForEachDictNode(Node):
    child_nodelists = ('nodelist_loop', 'nodelist_empty')

    def __init__(self, sequence, nodelist_loop, nodelist_empty=None):
        self.sequence = sequence
        self.nodelist_loop = nodelist_loop
        self.nodelist_empty = nodelist_empty or NodeList()

    def __repr__(self):
        return "<%s: in %s, tail_len: %d>" % (
            self.__class__.__name__,
            self.sequence,
            len(self.nodelist_loop),
        )

    def __iter__(self):
        yield from self.nodelist_loop
        yield from self.nodelist_empty

    def render(self, context):
        rendered = 0
        parentloop = context['foreachloop'] if 'foreachloop' in context else {}
        nodelist = []

        try:
            values = self.sequence.resolve(context, True)
        except VariableDoesNotExist:
            values = []
        if values is None:
            values = []

        with context.push():
            loop_dict = context['foreachloop'] = {'parentloop': parentloop}

            for i, item in enumerate(values):
                loop_dict['counter0'] = i
                loop_dict['counter'] = i + 1
                loop_dict['first'] = (i == 0)

                with context.push(**item):
                    for node in self.nodelist_loop:
                        nodelist.append(node.render_annotated(context))
                rendered += 1

        if rendered:
            return mark_safe(''.join(nodelist))
        return self.nodelist_empty.render(context)


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
    nodelist_loop = parser.parse(('empty', 'endforeachdict',))
    token = parser.next_token()
    if token.contents == 'empty':
        nodelist_empty = parser.parse(('endforeachdict',))
        parser.delete_first_token()
    else:
        nodelist_empty = None
    return ForEachDictNode(sequence, nodelist_loop, nodelist_empty)
