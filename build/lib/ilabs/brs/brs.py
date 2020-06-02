from __future__ import unicode_literals
import lxml.etree as et
import lxmlx.event as ev
import io
import os

BRS_NS = "http://innodatalabs.com/brs"

BRS_B = et.QName(BRS_NS, 'b').text
BRS_R = et.QName(BRS_NS, 'r').text
BRS_S = et.QName(BRS_NS, 's').text


def parse_brs(binary_data):
    '''
    Parses BRS XML and provides sanity validations
    '''
    if type(binary_data) is not bytes:
        raise RuntimeError('invalid XML document: expected data of type "bytes", received %r' % type(binary_data))

    if len(binary_data) < 4:
        raise RuntimeError('invalid XML document (too short)')

    if binary_data[:1] != b'<':
        raise RuntimeError('data is expected to start with "<". Please verify that the data does not contian BOM markers or leading space(s)')

    path = os.path.dirname(os.path.abspath(__file__))
    abs_schema_location = os.path.join(path, 'resources/BRS_XMLSchema_180417.xsd')

    with io.open(abs_schema_location, 'rb') as f:
        schema = et.XMLSchema(et.fromstring(f.read()))
    parser = et.XMLParser(encoding='UTF-8', huge_tree=True, schema=schema) # huge_tree: disable security restrictions and support very deep trees

    return et.fromstring(binary_data, parser=parser)


def record_from_tokens_and_iob_labels(tokens, labels):
    '''
    Generates BRS_R record from tokens and IOB labels, as XML event stream.
    To get XML element as a tree chunk, use ev.unscan().
    '''

    yield dict(type=ev.ENTER, tag=BRS_R)

    stack = []
    for text,label in zip(tokens, labels):
        assert len(stack) <= 1

        if label[0] == 'B':
            if stack: # B implicitly closes current sequence, if any
                stack.pop()
                yield dict(type=ev.EXIT)

            obj = dict(type=ev.ENTER, tag=BRS_S)
            if len(label) > 2:  # do not set "l" attribute if single-label decoding
                obj['attrib'] = {'l': label[2:]}

            stack.append(obj)
            yield obj

        elif label[0] == 'I':
            assert len(stack) == 1

        else:
            assert label == 'O'
            if stack:
                stack.pop()
                yield dict(type=ev.EXIT)

        yield dict(type=ev.TEXT, text=text)

    if stack:
        stack.pop()
        yield dict(type=ev.EXIT)

    yield dict(type=ev.EXIT)


def tokens_and_iob_labels_from_record(r, tokenizer):
    '''
    Given a BRS record and text tokenizer, parses the record and returns
    two lists: list of tokens, and list of corresponding IOB labels.
    '''
    assert r.tag == BRS_R, r

    inputs = []
    targets = []

    label = None
    first = True
    for obj,peer in ev.with_peer(ev.scan(r)):
        if obj['type'] == ev.TEXT:
            span = list(tokenizer(obj['text']))
            if span:
                inputs.extend(span)
                if label is None:
                    targets.extend(['O'] * len(span))
                elif first:
                    targets.extend(['B-' + label] + ['I-' + label]*(len(span)-1))
                    first = False
                else:
                    targets.extend(['I-' + label]*len(span))

        elif obj['type'] == ev.ENTER:
            if obj['tag'] == BRS_S:
                if label is not None:
                    raise RuntimeError('Nesting of <brs:s> not supported')
                label = obj['attrib']['l']
                first = True

        elif obj['type'] == ev.EXIT:
            if peer['tag'] == BRS_S:
                assert peer['attrib']['l'] == label
                label = None

    return inputs, targets
