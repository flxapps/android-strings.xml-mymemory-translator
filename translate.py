import base64
import html
import re
import xml.sax.saxutils as saxutils
import os

import lxml.etree
from translate import Translator

USER = "bob@example.com"
FILE = "strings.xml"
LANG_TO = "de"
LANG_FROM = "en"


def string_content(node):
    lxml.etree.strip_attributes(node, 'name', 'xmlns:tools')
    s = lxml.etree.tostring(node, encoding='unicode', with_tail=False).replace(
        'xmlns:tools="http://schemas.android.com/tools">', '')
    return html.unescape(s[s.index(node.tag) + 1 + len(node.tag): s.rindex(node.tag) - 2])


# replaces certain strings like placeholders (%s, %1$d, etc.)
# or line breaks with a html tag containing the originalstring
def create_placeholder(string):
    pattern = re.compile(r'( ?(?:%(?:[0-9]\$)?[sd]|[\r\n]+\s*|\\n|\\\"|<!\[CDATA\[|\s+]]>) ?)')
    for placeholder in re.findall(pattern, string):
        string = string.replace(
            placeholder,
            "<ph b64=\"" + base64.b64encode(placeholder.encode('ascii')).decode('ascii') + "\" />"
        )
    return string


def parse_placeholders(string):
    pattern = re.compile(r'( *<ph b64=\"([^\"]+)\" /> *)')
    for (placeholder, content) in re.findall(pattern, string):
        string = string.replace(placeholder, base64.b64decode(content.encode('ascii')).decode('ascii'))
    return string


def remove_children(node):
    for child in list(node):
        node.remove(child)


def get_translation(node):
    node.text = parse_placeholders(translator.translate(create_placeholder(string_content(node))))
    remove_children(node)
    return node


translator = Translator(from_lang=LANG_FROM, to_lang=LANG_TO, email=USER)

parser = lxml.etree.XMLParser(ns_clean=True, strip_cdata=False, remove_comments=True)
tree = lxml.etree.parse(FILE, parser)
root = tree.getroot()

for i in range(len(root)):
    isTranslatable = root[i].get('translatable')

    if isTranslatable == 'false':
        continue

    name = root[i].get('name')
    print(str(name) + "…\n")

    if root[i].tag == 'string':
        get_translation(root[i])

    if root[i].tag == 'string-array':
        for j in range(len(root[i])):
            if root[i][j].tag == 'item':
                isTranslatable = root[i][j].get('translatable')
                if isTranslatable != 'false':
                    get_translation(root[i][j])

    if name is not None:
        root[i].set('name', name)

dir_path = "values-" + LANG_TO
if os.path.isdir(dir_path) is False:
    os.mkdir(dir_path)

file_path = dir_path + "/" + FILE
tree.write(file_path, encoding='utf-8')

# post-processing: unescape html characters
with open(file_path) as f:
    file_str = f.read()
with open(file_path, "w") as f:
    f.write(saxutils.unescape(file_str).replace(" & ", " &amp; "))
