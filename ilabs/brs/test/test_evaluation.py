import pytest
from ilabs.brs import evaluation
import lxml.etree as et
import lxmlx.event as ev
from ilabs.brs import parse_brs
import unittest




BRS_SAMPLE_11 = b"""<b xmlns='http://innodatalabs.com/brs'>
                <r>Sample <s l='record'>record</s>- <s l='refno'>1</s></r>
                <r>Sample <s l='record'>record</s>- <s l='refno'>2</s></r>
                <r>Invalid <s l='record'>record</s>- <s l='refno'>3</s></r>
                </b>"""

BRS_SAMPLE_12 = b"""<i:b xmlns:i='http://innodatalabs.com/brs'>
                <i:r>Sample <i:s l='record'>record</i:s>- <i:s l='refno'>1</i:s></i:r>
                <i:r>Sample <i:s l='record'>record</i:s>- <i:s l='refno'>2</i:s></i:r>
                <i:r>Invalid <i:s l='record'>record-</i:s> <i:s l='refno'>3</i:s></i:r>
                </i:b>
                    """
BRS_SAMPLE_21 = b"""<i:b xmlns:i='http://innodatalabs.com/brs'>
                    <i:r><div>Innodata labs</div><div>Here is <p>some <i:s l='sample'>sample</i:s> data</p><p>Some more <i:s l='sample'>sample</i:s> <i:s l='data'>data</i:s> </p></div>
                    </i:r></i:b>"""

class TestEvaluation(unittest.TestCase):

    def test_record_to_set(self):
        ideal_set = {(7, 13, 'record'), (15, 16, 'refno')}
        records = evaluation.records(parse_brs(BRS_SAMPLE_11))
        test_set = evaluation.record_to_set(ev.scan(next(records)))
        assert test_set == ideal_set
        ideal_set = {(26, 32, 'sample'), (47, 53, 'sample'), (54, 58, 'data')}
        records = evaluation.records(parse_brs(BRS_SAMPLE_21))
        test_set = evaluation.record_to_set(ev.scan(next(records)))
        assert test_set == ideal_set


    def test_evaluation(self):

        test_sample_11 = parse_brs(BRS_SAMPLE_11)
        test_sample_12 = parse_brs(BRS_SAMPLE_12)
        test_sample_21 = parse_brs(BRS_SAMPLE_21)
        result = evaluation.evaluate(test_sample_11, test_sample_12)

        assert isinstance(result, dict)

        assert result['gold_tag_count'] == 6
        assert result['tp'] == 5
        assert result['fp'] == 1
        assert result['fn'] == 1

        self.assertRaises(TypeError, evaluation.evaluate, 'invalid_input_type', test_sample_11)
        self.assertRaises(ValueError, evaluation.evaluate, et.fromstring('<b>Invalid</b>'), test_sample_11)
        self.assertRaises(ValueError, evaluation.evaluate, test_sample_11, test_sample_21)
