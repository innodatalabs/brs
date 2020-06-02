from ilabs.brs.util import adict

def test_smoke():
    x = adict(foo='foo', bar='bar')

    assert x.foo == 'foo'
    assert x.bar == 'bar'
    assert x['foo'] == 'foo'
    assert x['bar'] == 'bar'

def test_dict():
    x = adict(foo='foo', bar='bar')

    x[3] = 5
    x['foo'] == 'foo'
    assert x['bar'] == 'bar'
    assert x[3] == 5
