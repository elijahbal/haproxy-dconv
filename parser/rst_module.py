import os
import cgi
import datetime
import re

from mako.lookup import TemplateLookup
from mako.exceptions import TopLevelLookupException

import parser

import os
import cgi
import datetime
import re

from mako.lookup import TemplateLookup
from mako.exceptions import TopLevelLookupException

import parser
# The parser itself

def convert_all_rst(infiles, outdir, base=''):
    converted = []
    menu = []
    for infile in infiles:
        basefile = os.path.basename(infile).replace(".txt", ".html")
        outfile = os.path.join(outdir, basefile)

        pctxt = parser.PContext(
            TemplateLookup(
                directories=[
                    'templates'
                ]
            )
        )
        data = convert_rst(pctxt, infile, outfile, base)
        converted.append((outfile, data))
        menu.append((basefile, data['pctxt'].context['headers']['subtitle']))

    for item in converted:
        outfile, data = item
        data['menu'] = menu
        print("Exporting to %s..." % outfile, file=sys.stderr)
        template = pctxt.templates.get_template('template.html')
        with open(outfile, 'w') as fd:
            print(template.render(**data), file=fd)



def convert_rst(pctxt, infile, outfile, base='', version='', haproxy_version=''):
    global document, keywords, keywordsCount, chapters, keyword_conflicts

    if base and base[:-1] != '/':
        base += '/'

    with open(infile) as fd:
        data = [line.replace("\t", " "*8).rstrip() for line in fd.readlines()]

    parsers = parser.converter.init_parsers(pctxt)

    pctxt.context = {
            'headers': {},
            'document': "",
            'base': base,
    }

    keywords = {}
    keywordsCount = {}

    specialSections = {
            "default": {
                    "hasKeywords": True,
            },
            "4.1": {
                    "hasKeywords": True,
            },
    }

    print("Importing %s..." % infile, file=sys.stderr)
    section_list, chapters, hasSummary, i, nblines = parser.sections.build_sections(data)

    pctxt.keywords = keywords
    pctxt.keywordsCount = keywordsCount
    pctxt.chapters = chapters

    chapterIndexes = sorted(list(chapters.keys()), key=lambda chapter: list(map(int, chapter.split('.'))))
    document = ""

    chapters, chapterIndexes = parser.sections.completeSummary(section_list, chapters, chapterIndexes)

    for section in section_list:
        details = section["details"]
        pctxt.details = details
        level = details["level"]
        title = details["title"]
        content = section["content"].rstrip()

        print("Parsing chapter %s..." % title, file=sys.stderr)

        if (title == "Summary") or (title and not hasSummary):
            summaryTemplate = pctxt.templates.get_template('summary.html')
            parser.converter.documentAppend(summaryTemplate.render(
                pctxt=pctxt,
                chapters=chapters,
                chapterIndexes=chapterIndexes,
            ))
            if title and not hasSummary:
                hasSummary = True
            else:
                continue

        if title:
            parser.converter.documentAppend(
                '<a class="anchor" id="%s" name="%s"></a>' %
                (details["chapter"], details["chapter"]))
            if level == 1:
                parser.converter.documentAppend("<div class=\"page-header\">", False)

            parser.converter.documentAppend(
                '<h%d id="chapter-%s" data-target="%s"><small><a class="small" href="#%s">%s.</a></small> %s</h%d>' %
                (level, details["chapter"], details["chapter"], details["chapter"], details["chapter"], cgi.escape(title, True), level))

            if level == 1:
                parser.converter.documentAppend("</div>", False)

        if content:
            if False and title:
                # Display a navigation bar
                parser.converter.documentAppend('<ul class="well pager">')
                parser.converter.documentAppend('<li><a href="#top">Top</a></li>', False)
                index = chapterIndexes.index(details["chapter"])
                if index > 0:
                    parser.converter.documentAppend('<li class="previous"><a href="#%s">Previous</a></li>' % chapterIndexes[index - 1], False)
                if index < len(chapterIndexes) - 1:
                    parser.converter.documentAppend('<li class="next"><a href="#%s">Next</a></li>' % chapterIndexes[index + 1], False)
                parser.converter.documentAppend('</ul>', False)
            content = cgi.escape(content, True)
            content = re.sub(r'section ([0-9]+(.[0-9]+)*)', r'<a href="#\1">section \1</a>', content)

            pctxt.set_content(content)

            if not title:
                lines = pctxt.get_lines()
                pctxt.context['headers'] = {
                    'title': '',
                    'subtitle': '',
                    'version': '',
                    'author': '',
                    'date': ''
                }
                if re.match("^-+$", pctxt.get_line().strip()):
                    # Try to analyze the header of the file, assuming it follows
                    # those rules :
                    # - it begins with a "separator line" (several '-' chars)
                    # - then the document title
                    # - an optional subtitle
                    # - a new separator line
                    # - the version
                    # - the author
                    # - the date
                    pctxt.next()
                    pctxt.context['headers']['title'] = pctxt.get_line().strip()
                    pctxt.next()
                    subtitle = ""
                    while not re.match("^-+$", pctxt.get_line().strip()):
                        subtitle += " " + pctxt.get_line().strip()
                        pctxt.next()
                    pctxt.context['headers']['subtitle'] += subtitle.strip()
                    if not pctxt.context['headers']['subtitle']:
                        # No subtitle, try to guess one from the title if it
                        # starts with the word "HAProxy"
                        if pctxt.context['headers']['title'].startswith('HAProxy '):
                            pctxt.context['headers']['subtitle'] = pctxt.context['headers']['title'][8:]
                            pctxt.context['headers']['title'] = 'HAProxy'
                    pctxt.next()
                    pctxt.context['headers']['version'] = pctxt.get_line().strip()
                    pctxt.next()
                    pctxt.context['headers']['author'] = pctxt.get_line().strip()
                    pctxt.next()
                    pctxt.context['headers']['date'] = pctxt.get_line().strip()
                    pctxt.next()
                    if haproxy_version:
                        pctxt.context['headers']['version'] = 'version ' + haproxy_version

                    # Skip header lines
                    pctxt.eat_lines()
                    pctxt.eat_empty_lines()

            parser.converter.documentAppend('<div>', False)

            delay = []
            while pctxt.has_more_lines():
                try:
                    specialSection = specialSections[details["chapter"]]
                except:
                    specialSection = specialSections["default"]

                line = pctxt.get_line()
                if i < nblines - 1:
                    nextline = pctxt.get_line(1)
                else:
                    nextline = ""

                oldline = line
                pctxt.stop = False
                for one_parser in parsers:
                    line = one_parser.parse(line)
                    if pctxt.stop:
                        break
                if oldline == line:
                    # nothing has changed,
                    # delays the rendering
                    if delay or line != "":
                        delay.append(line)
                    pctxt.next()
                elif pctxt.stop:
                    while delay and delay[-1].strip() == "":
                        del delay[-1]
                    if delay:
                        parser.remove_indent(delay)
                        parser.converter.documentAppend('<pre class="text">%s\n</pre>' % "\n".join(delay), False)
                    delay = []
                    parser.converter.documentAppend(line, False)
                else:
                    while delay and delay[-1].strip() == "":
                        del delay[-1]
                    if delay:
                        parser.remove_indent(delay)
                        parser.converter.documentAppend('<pre class="text">%s\n</pre>' % "\n".join(delay), False)
                    delay = []
                    parser.converter.documentAppend(line, True)
                    pctxt.next()

            while delay and delay[-1].strip() == "":
                del delay[-1]
            if delay:
                parser.remove_indent(delay)
                parser.converter.documentAppend(
                    "<pre class=\"text\">{}\n</pre>".format("\n".join(delay)),
                    False
                )
            delay = []
            parser.converter.documentAppend('</div>')

    if not hasSummary:
        summaryTemplate = pctxt.templates.get_template('summary.html')
        print(chapters)
        document = summaryTemplate.render(
            pctxt=pctxt,
            chapters=chapters,
            chapterIndexes=chapterIndexes,
        ) + document


    # Log warnings for keywords defined in several chapters
    keyword_conflicts = {}
    for keyword in keywords:
        keyword_chapters = list(keywords[keyword])
        keyword_chapters.sort()
        if len(keyword_chapters) > 1:
            print("Multi section keyword : \"{}\" in chapters {}".
                  format(keyword, list(keyword_chapters)), file=sys.stderr)
            keyword_conflicts[keyword] = keyword_chapters

    keywords = list(keywords)
    keywords.sort()

    parser.converter.createLinks()

    # Add the keywords conflicts to the keywords list to make
    # them available in the search form and remove the original
    # keyword which is now useless
    for keyword in keyword_conflicts:
        sections = keyword_conflicts[keyword]
        offset = keywords.index(keyword)
        for section in sections:
            keywords.insert(offset, "{} ({})".format(keyword, chapters[section]['title']))
            offset += 1
        keywords.remove(keyword)

    try:
        footerTemplate = pctxt.templates.get_template('footer.html')
        footer = footerTemplate.render(
            pctxt=pctxt,
            headers=pctxt.context['headers'],
            document=document,
            chapters=chapters,
            chapterIndexes=chapterIndexes,
            keywords=keywords,
            keywordsCount=keywordsCount,
            keyword_conflicts=keyword_conflicts,
            version=version,
            date=datetime.datetime.now().strftime("%Y/%m/%d"),
        )
    except TopLevelLookupException:
        footer = ""

    return {
            'pctxt': pctxt,
            'headers': pctxt.context['headers'],
            'base': base,
            'document': document,
            'chapters': chapters,
            'chapterIndexes': chapterIndexes,
            'keywords': keywords,
            'keywordsCount': keywordsCount,
            'keyword_conflicts': keyword_conflicts,
            'version': version,
            'date': datetime.datetime.now().strftime("%Y/%m/%d"),
            'footer': footer
    }
