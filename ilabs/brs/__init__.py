__version__      = '1.0.0'
__description__  = 'Innodata BRS schema and utilities'
__author__       = 'Mike Kroutikov'
__author_email__ = 'mkroutikov@innodata.com'
__url__          = 'http://innodata.com'
__keywords__     = 'inline tagging xml schema'


from .brs import (
    parse_brs,
    record_from_tokens_and_iob_labels,
	BRS_B, BRS_R, BRS_NS,
    tokens_and_iob_labels_from_record
)