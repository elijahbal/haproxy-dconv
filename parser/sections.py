import re
import sys


def getTitleDetails(string):
    my = re.search("(^(\d+\.?)+)\s", string)
    if my and my.group(0):  # case of a number in the section title
        chap_num_sequence = [num for num in my.group(1).split(".") if num]
        chap_number = ".".join(chap_num_sequence)
        title = string[my.end(0):]
    else:
        chap_num_sequence = []
        chap_number = ""
        title = string
    title=title.rstrip().lstrip(' ').rstrip(' ')
    level = max(1, len(chap_num_sequence))
    toplevel = chap_num_sequence[0] if chap_num_sequence else False

    return {"title": title, "chapter": chap_number,
            "level": level, "toplevel": toplevel}


def build_sections(data):
    sections = []
    chapters = {}
    currentSection = {
            "details": getTitleDetails(""),
            "content": "",
    }

    i = j = 0
    nblines = len(data)
    while i < nblines:
        line = data[i].rstrip()
        if i < nblines - 1:
            next = data[i + 1].rstrip()
        else:
            next = ""
        if (line == "Summary" or re.match("^[0-9].*", line)) \
                and (len(next) > 0) and (next[0] == '-') \
                and ("-" * len(line)).startswith(next):
            # in this case, we are at a section header or at the Summary line
            sections.append(currentSection)
            # we store the section here but we can do better --
            # we can fetch the level of that section
            currentSection = {
                "details": getTitleDetails(line),
                "content": "",
            }
            j = 0
            i += 1  # Skip underline
            while not data[i + 1].rstrip():
                i += 1  # Skip empty lines

        else:
            if len(line) > 80:
                print("Line `%i' exceeds 80 columns" % (i + 1), file=sys.stderr)

            currentSection["content"] = currentSection["content"] + line + "\n"
            j += 1
            if currentSection["details"]["title"] == "Summary" and line != "":
                hasSummary = True
                details = getTitleDetails(line)
                if details["chapter"]:
                    chapters[details["chapter"]] = details
        i += 1
    sections.append(currentSection)
    return sections, chapters, hasSummary, i, nblines


def completeSummary(sectionList, chapters, chapterIndexes):
    # Complete the summary
    for section in sectionList:
        meta_information = section["details"]
        if meta_information.get('title') \
                and meta_information.get('chapter') and \
                        meta_information['chapter'] not in chapters:
            print("Missing chapter '%s' to the summary" % meta_information["title"], file=sys.stderr)
            chapters[meta_information["chapter"]] = meta_information
            chapterIndexes = sorted(chapters.keys())
    return chapters, chapterIndexes