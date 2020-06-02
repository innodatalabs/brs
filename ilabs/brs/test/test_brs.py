from __future__ import unicode_literals
import lxml.etree as et
import lxmlx.event as ev
import pytest
import os
from ilabs.brs import parse_brs, record_from_tokens_and_iob_labels, \
	BRS_B, BRS_R, BRS_NS, tokens_and_iob_labels_from_record
import contextlib
import re

@contextlib.contextmanager
def raises_text(exc_type, regexp):
	with pytest.raises(Exception) as e:
		yield
	if not re.search(re.escape(regexp), str(e.value)):
		raise AssertionError('Exception text %r did not match expected pattern %r' % (e.value, regexp))


BAD_SCHEMA = b'''<i:b xmlns:i="http://innodatalabs.com/brs">no text between i:r tags is allowed!\
<i:r>\
<i:s l="lab">Innodata Labs</i:s>, <i:s l="institution">Innodata inc.</i:s>, <i:s l="city">Hackensack</i:s>, <i:s l="state">New Jersey</i:s>, <i:s l="country">USA</i:s>\
</i:r>\
</i:b>'''

BOM = b'\xff\xfeXX'
BOM_BE = b'\xfe\xffXX'

GOOD_SCHEMA_1 = b'''<i:b xmlns:i="http://innodatalabs.com/brs">\
<i:r>\
<i:s l="lab">Innodata Labs</i:s>, <i:s l="institution">Innodata inc.</i:s>, <i:s l="city">Hackensack</i:s>, <i:s l="state">New Jersey</i:s>, <i:s l="country">USA</i:s>\
</i:r>
</i:b>'''

GOOD_SCHEMA_2 = b'''<?xml version="1.0" encoding="utf-8"?><i:b xmlns:i="http://innodatalabs.com/brs">\
<i:r>\
<i:s l="lab">Innodata Labs</i:s>, <i:s l="institution">Innodata inc.</i:s>, <i:s l="city">Hackensack</i:s>, <i:s l="state">New Jersey</i:s>, <i:s l="country">USA</i:s>\
</i:r>\
</i:b>'''

BAD_XML = b'''<i:b xmlns:i="http://innodatalabs.com/brs"><i:r>\
<i:s l="lab">Innodata Labs</i:s>, <i:s l="institution">Innodata inc.</i:s>, <i:s l="city">Hackensack</i:s>, <i:s l="state">New Jersey, <i:s l="country">USA</i:s>\
</i:r></i:b>'''

VALID_UTF_8 = b'<?xml version="1.0" encoding="utf-8"?><root>\u2163</root>'


def test_parse_brs():

	with raises_text(RuntimeError, 'expected data of type "bytes"'):
		parse_brs('<a />')

	with raises_text(RuntimeError, 'invalid XML document (too short)'):
		parse_brs(b'')

	with raises_text(RuntimeError, 'data is expected to start with "<"'):
		parse_brs(BOM)

	with raises_text(RuntimeError, 'data is expected to start with "<"'):
		parse_brs(BOM_BE)

	with raises_text(RuntimeError, "Element '{http://innodatalabs.com/brs}b': Character content other than whitespace is not allowed because the content type is 'element-only'."):
		parse_brs(BAD_SCHEMA)

	with pytest.raises(et.XMLSyntaxError):
		parse_brs(BAD_XML)

	with raises_text(RuntimeError, "Element 'root': No matching global declaration available for the validation root."):
		parse_brs(VALID_UTF_8)

	xml = parse_brs(GOOD_SCHEMA_1)
	assert xml.tag == BRS_B
	assert len(xml) == 1
	assert xml[0].tag == BRS_R

	xml = parse_brs(GOOD_SCHEMA_2)
	assert xml.tag == BRS_B
	assert len(xml) == 1
	assert xml[0].tag == BRS_R

def test_record_from_tokens_and_iob_labels():

    r = ev.unscan(record_from_tokens_and_iob_labels(
        ['Hello', ',', ' ', 'beautiful', ' ',      'world',  '!'],
        ['O',     'O', 'O', 'B-word',    'I-word', 'I-word', 'O'],
    ), nsmap = {None: BRS_NS})

    model = b'<r xmlns="http://innodatalabs.com/brs">Hello, <s l="word">beautiful world</s>!</r>'
    result = et.tostring(r)
    if model != result:
        print(model)
        print(result)
        assert False, 'Discrepancy'


def tokenzier(text):
	offset = 0
	for mtc in re.finditer(r'[^\W_]+', text):
		s, e = mtc.start(), mtc.end()
		if offset < s:
			for c in text[offset:s]:
				yield c
		yield text[s:e]
		offset = e
	for c in text[offset:]:
		yield c

def test_tokens_and_iob_labels_from_record():

	r = et.fromstring(b'<r xmlns="http://innodatalabs.com/brs">Hello, <s l="word">beautiful world</s>!</r>')
	tokens, labels = tokens_and_iob_labels_from_record(r, tokenzier)
	assert tokens == ['Hello', ',', ' ', 'beautiful', ' ',      'world',  '!']
	assert labels == ['O',     'O', 'O', 'B-word',    'I-word', 'I-word', 'O']


def test_tokens_and_iob_labels_from_record_bug0():
	r = et.fromstring('''<brs:r xmlns:brs="http://innodatalabs.com/brs"><brs:s l="au">Christian, P. D.</brs:s> <brs:s l="year">1983</brs:s>. \
<brs:s l="title">Water balance in <i>Monodelphis domestica</i></brs:s></brs:r>'''.encode())
	tokens, labels = tokens_and_iob_labels_from_record(r, tokenzier)
	assert tokens == [
		'Christian', ',', ' ', 'P', '.', ' ', 'D',  '.', ' ', 
		'1983', '.', ' ', 
		'Water', ' ', 'balance', ' ', 'in', ' ', 'Monodelphis', ' ', 'domestica'
	]
	assert labels == [
		'B-au', 'I-au', 'I-au', 'I-au', 'I-au', 'I-au', 'I-au', 'I-au', 'O',
		'B-year', 'O', 'O',
		'B-title', 'I-title', 'I-title', 'I-title', 'I-title', 'I-title', 'I-title', 'I-title', 'I-title'
	]
