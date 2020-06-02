# Innodata BRS schema and related utils

BRS schema (Block-Record-Span) is used to mark inline entities in text and XML documents.

Namespace is:
```
http://innodatalabs.com/brs
```

## Validating BRS parser

```python
from ilabs.brs import parse_brs

xml_text = b'''\
<i:b xmlns:i="http://innodatalabs.com/brs">
<i:r>Hello, <i:s l="name">Mike</i:s></i:r>
</i:b>
'''

xml = parse_brs(xml_text)  # this will throw if input is not a valid BRS
...
```

## Developing

```
pip install -r requirements.txt wheel pytest
PYTHONPATH=. pytest .

python setup.py bdist_wheel
```
