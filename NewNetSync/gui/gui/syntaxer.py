#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import sys
from PySide2 import QtCore, QtGui

if __name__ == '__main__':
    import xmlToDict
else:
    from gui import xmlToDict


def format(color, style=''):
    """
    Return a QtGui.QTextCharFormat with the given attributes.
    """
    _color = QtGui.QColor()
    if type(color) is not str:
        _color.setRgb(color[0], color[1], color[2])
    else:
        _color.setNamedColor(color)

    _format = QtGui.QTextCharFormat()
    _format.setForeground(_color)
    if 'bold' in style:
        _format.setFontWeight(QtGui.QFont.Bold)
    if 'italic' in style:
        _format.setFontItalic(True)

    return _format


# Syntax styles that can be shared by all languages

STYLES = {
    'keyword': format([200, 120, 50], 'bold'),
    'function': format([255, 1, 204]),
    'operator': format([150, 150, 150]),
    'brace': format('darkGray'),
    'defclass': format([220, 220, 255], 'bold'),
    'string': format([20, 110, 100]),
    'string2': format([30, 120, 110]),
    'comment': format([128, 128, 128]),
    'self': format([150, 85, 140], 'italic'),
    'numbers': format([100, 150, 190]),
}


class SQLHighlighter(QtGui.QSyntaxHighlighter):
    '''Syntax highlighter for the SQL language.
    '''

    # operators
    operators = [
        # Comparing
        '=',
        '!=',
        '<>',
        '<',
        '<=',
        '>',
        '>=',
        # Arithmetic
        '\+',
        '-',
        '\*',
        '/',
        '//',
        '\%',
        '\*\*',
    ]

    # Braces
    braces = [
        '\(',
        '\)',
    ]

    functions, keywords = xmlToDict.getXML()
    functions += [fn.lower() for fn in functions]
    keywords += [key.lower() for key in keywords]

    def __init__(self, document):
        QtGui.QSyntaxHighlighter.__init__(self, document)

        rules = []
        # Keyword, operator, and brace rules
        rules += [(r'\b%s\b' % w, 0, STYLES['keyword'])
                  for w in SQLHighlighter.keywords]
        rules += [(r'%s' % o, 0, STYLES['operator'])
                  for o in SQLHighlighter.operators]
        rules += [(r'%s' % b, 0, STYLES['brace'])
                  for b in SQLHighlighter.braces]
        rules += [(r'%s' % f, 0, STYLES['function'])
                  for f in SQLHighlighter.functions]

        # All other rules
        rules += [
            # Double-quoted string, possibly containing escape sequences
            (r'"[^"\\]*(\\.[^"\\]*)*"', 0, STYLES['string']),
            # Single-quoted string, possibly containing escape sequences
            (r"'[^'\\]*(\\.[^'\\]*)*'", 0, STYLES['string']),

            # From '#' until a newline
            (r'---[^\n]*', 0, STYLES['comment']),

            # Numeric literals
            (r'\b[+-]?[0-9]+[lL]?\b', 0, STYLES['numbers']),
            (r'\b[+-]?0[xX][0-9A-Fa-f]+[lL]?\b', 0, STYLES['numbers']),
            (r'\b[+-]?[0-9]+(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?\b', 0,
             STYLES['numbers']),
        ]

        # Build a QtCore.QRegExp for each pattern
        self.rules = [(QtCore.QRegExp(pat), index, fmt)
                      for (pat, index, fmt) in rules]

    def highlightBlock(self, text):
        """Apply syntax highlighting to the given block of text.
        """
        # Do other syntax formatting
        for expression, nth, format in self.rules:
            index = expression.indexIn(text, 0)

            while index >= 0:
                # We actually want the index of the nth match
                index = expression.pos(nth)
                length = len(expression.cap(nth))
                self.setFormat(index, length, format)
                index = expression.indexIn(text, index + length)

        self.setCurrentBlockState(0)
