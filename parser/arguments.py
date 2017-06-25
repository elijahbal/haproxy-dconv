import sys
import re
import parser

class ArgumentParser(parser.Parser):
    def __init__(self, pctxt):
        parser.Parser.__init__(self, pctxt)

    def parse(self, line):
        pctxt = self.pctxt

        result = re.search(r'(Arguments? *:)', line)
        if result:
            label = result.group(0)
            desc = re.sub(r'.*Arguments? *:', '', line).strip()
            indent = parser.get_indent(line)
            pctxt.next()
            pctxt.eat_empty_lines()
            arglines = []
            if desc != "none":
                add_empty_lines = 0
                while pctxt.has_more_lines() and (parser.get_indent(pctxt.get_line()) > indent):
                    for j in range(0, add_empty_lines):
                        arglines.append("")
                    arglines.append(pctxt.get_line())
                    pctxt.next()
                    add_empty_lines = pctxt.eat_empty_lines()
                if arglines:
                    parser.remove_indent(arglines)

            pctxt.stop = True

            template = pctxt.templates.get_template("parser/arguments.tpl")
            return template.render(
                pctxt=pctxt,
                label=label,
                desc=desc,
                content=arglines,
            )
        return line
