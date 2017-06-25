"""
This module is made of the various high-level method used to effectively
convert the Haproxy documentation into a suitable form
"""

import sys
from urllib.parse import quote

import parser
import parser.arguments
import parser.underline
import parser.keyword
import parser.example
import parser.table
import parser.seealso
import parser.sections


# Parse the whole document to insert links on keywords
def createLinks(document, keywords, keywordsCount, keyword_conflicts, chapters):
    print("Generating keywords links...", file=sys.stderr)

    delimiters = [
        dict(start='&quot;', end='&quot;', multi=True),
        dict(start='- ', end='\n', multi=False),
    ]

    for keyword in keywords:
        keywordsCount[keyword] = 0
        for delimiter in delimiters:
            keywordsCount[keyword] += document.count(
                                        delimiter['start'] +
                                        keyword +
                                        delimiter['end']
                                      )
        if (keyword in keyword_conflicts) and (not keywordsCount[keyword]):
            # The keyword is never used, we can remove it from the conflicts list
            del keyword_conflicts[keyword]

        if keyword in keyword_conflicts:
            chapter_list = ""
            for chapter in keyword_conflicts[keyword]:
                chapter_list += '<li><a href="#%s">%s</a></li>' % (quote("%s (%s)" % (keyword, chapters[chapter]['title'])), chapters[chapter]['title'])
            for delimiter in delimiters:
                if delimiter['multi']:
                    document = document.replace(
                        delimiter['start'] + keyword + delimiter['end'],
                        delimiter['start'] + '<span class="dropdown">' +
                        '<a class="dropdown-toggle" data-toggle="dropdown" href="#">' +
                        keyword +
                        '<span class="caret"></span>' +
                        '</a>' +
                        '<ul class="dropdown-menu">' +
                        '<li class="dropdown-header">This keyword is available in sections :</li>' +
                        chapter_list +
                        '</ul>' +
                        '</span>' + delimiter['end']
                    )
                else:
                    document = document.replace(delimiter['start'] +
                               keyword + delimiter['end'], delimiter['start'] +
                               '<a href="#' + quote(keyword) + '">' + keyword +
                               '</a>' + delimiter['end'])
        else:
            for delimiter in delimiters:
                document = document.replace(delimiter['start'] +
                                            keyword + delimiter['end'],
                                            delimiter['start'] +
                                            '<a href="#' + quote(keyword) + '">' +
                                            keyword + '</a>' +
                                            delimiter['end'])

        if keyword.startswith("option "):
            shortKeyword = keyword[len("option "):]
            keywordsCount[shortKeyword] = 0
            for delimiter in delimiters:
                keywordsCount[keyword] += document.count(delimiter['start'] + shortKeyword + delimiter['end'])
            if (shortKeyword in keyword_conflicts) and (not keywordsCount[shortKeyword]):
            # The keyword is never used, we can remove it from the conflicts list
                del keyword_conflicts[shortKeyword]
            for delimiter in delimiters:
                document = document.replace(delimiter['start'] + shortKeyword + delimiter['start'], delimiter['start'] + '<a href="#' + quote(keyword) + '">' + shortKeyword + '</a>' + delimiter['end'])
    return document, keywords, keywordsCount, keyword_conflicts, chapters


def documentAppend(document, text, retline = True):
    document += text
    if retline:
        document += "\n"
    return document

def init_parsers(pctxt):
    return [
        parser.underline.UnderlineParser(pctxt),
        parser.arguments.ArgumentParser(pctxt),
        parser.seealso.SeeAlsoParser(pctxt),
        parser.example.ExampleParser(pctxt),
        parser.table.TableParser(pctxt),
        parser.keyword.KeyWordParser(pctxt),
    ]