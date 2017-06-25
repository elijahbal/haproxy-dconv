import pytest

from parser import converter

@pytest.mark.parametrize(
    "input_string,expected",
    [("3.2.1. foobar foo", {'title': 'foobar foo', 'chapter': '3.2.1', 'level': 3, 'toplevel': '3'}),
     ("3.2.1. foobar. foo?", {'title': 'foobar. foo?', 'chapter': '3.2.1', 'level': 3, 'toplevel': '3'}),
     ("1.2. foobar foo.", {'title': 'foobar foo.', 'chapter': '1.2', 'level': 2, 'toplevel': '1'}),
     ("2.2 foobar foo.", {'title': 'foobar foo.', 'chapter': '2.2', 'level': 2, 'toplevel': '2'}),
     ("     Summary  ", {'title': 'Summary', 'chapter': '', 'level': 1, 'toplevel': False}),
     ("Summary  ", {'title': 'Summary', 'chapter': '', 'level': 1, 'toplevel': False}),
     ("", {'title': '', 'chapter': '', 'level': 1, 'toplevel': False})
     ]
)
def test_getTitleDetails(input_string, expected):
    my = converter.getTitleDetails(input_string)
    assert my == expected