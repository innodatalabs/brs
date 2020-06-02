import lxmlx.event as ev
from .brs import BRS_B, BRS_S, BRS_R
from .util import adict
import collections
import lxml.etree as et


def records(brs):
    for record in brs:
        yield record


def record_to_set(record):
    offset = 0
    annotations = []
    stack = []
    for obj, peer in ev.with_peer(record):
        if obj['type'] == ev.TEXT:
            offset += len(obj['text'])
        elif obj['type'] == ev.ENTER:
            if obj['tag'] == BRS_S:
                a = adict(tag=obj.get('attrib', {}).get('l'), start=offset, end=None)
                stack.append(a)
                annotations.append(a)
        elif obj['type'] == ev.EXIT:
            if peer['tag'] == BRS_S:
                a = stack.pop()
                a.end = offset
    return set((a.start, a.end, a.tag) for a in annotations)


def evaluate(golden_records, predicted_records, confidence=10.0):
    """Evaluate tagger service result against golden truth

    param golden_records: XML with "true" labeling in BRS format
        type golden_records: Parsed XML

    param predicted_records: XML with predicted records in BRS format
        type predicted_records: Parsed XML
    param confidence: Record level confidence threshold value
        type confidence: float

    Note that number of records in both files must be the same, and each record in predicted file must have the corresponding record in the golden_records.

    returns: Evaluation statistics
        rtype: dict
        contents:
            record_count:           Number of records evaluated
            gold_tag_count:         Number of annotations in golden records
            pred_tag_count:         Number of annotations in predicted records
            tp:                     Number of true positives
            fp:                     Number of false positives
            fn:                     Number of false negatives
            correct:                Number of correct records
            incorrect:              Number of incorrect records
            high_conf_records       Number of records in high confidence channel
            low_conf_records        Number of records in low confidence channel
            high_conf_error_rate    Error rate in high confidence channel
            low_conf_error_rate     Error rate in low confidence channel
            record_accuracy:        Record level accuracy of tagger service
            tag_accuracy:           Tag level accuracy of tagger service
            precision:              Precision measure of tagger service
            recall:                 recall measure of tagger service
            f1-score:               f1-score of tagger service"""

    if not (isinstance(golden_records, et._Element) and isinstance(predicted_records, et._Element)):
        raise TypeError('Invalid input object type. Expected object of type {}'.format(et._Element))

    if not ((golden_records.tag == BRS_B) and (predicted_records.tag == BRS_B)):
        raise ValueError('Invalid XML Format. Expected XML in BRS format')

    if not (len(golden_records) == len(predicted_records)):
        raise ValueError('Received mismatched number of golden records and predicted records. Number of golden records and predicted records must be same')

    golden_recorder = records(golden_records)
    prediction_recorder = records(predicted_records)

    stats = collections.defaultdict(int)

    for gold, pred in zip(golden_recorder, prediction_recorder):
        true_annotations = record_to_set(ev.scan(gold))
        predicted_annotations = record_to_set(ev.scan(pred))
        score = float(pred.attrib.get('c', 10.0))

        if score >= confidence:
            stats['high_conf_records'] += 1
        else:
            stats['low_conf_records'] += 1

        num_tp = len(predicted_annotations & true_annotations)
        num_fp = len(predicted_annotations - true_annotations)
        num_fn = len(true_annotations - predicted_annotations)

        stats['record_count'] += 1
        stats['gold_tag_count'] += len(true_annotations)
        stats['pred_tag_count'] += len(predicted_annotations)
        stats['tp'] += num_tp
        stats['fp'] += num_fp
        stats['fn'] += num_fn

        if not (num_fp == 0 and num_fn == 0):
            stats['incorrect'] += 1
            if score >= confidence:
                stats['incorrect_high_conf_records'] += 1
            else:
                stats['incorrect_low_conf_records'] += 1
        else:
            stats['correct'] += 1

    stats['high_conf_error_rate'] = 100 * stats['incorrect_high_conf_records'] / (stats['high_conf_records'] + 0.1e-8)
    stats['low_conf_error_rate'] = 100 * stats['incorrect_low_conf_records'] / (stats['low_conf_records'] + 0.1e-8)
    stats['record_accuracy'] = 100 * stats['correct'] / (stats['record_count'] + 0.1e-8)
    stats['tag_accuracy'] = 100 * stats['tp'] / (stats['gold_tag_count'] + 0.1e-8)
    precision = stats['tp'] / (stats['tp'] + stats['fp'] + 1.e-8)
    recall = stats['tp'] / (stats['tp'] + stats['fn'] + 1.e-8)
    stats['precision'] = precision * 100
    stats['recall'] = recall * 100
    stats['f1-score'] = (2.0 * precision * recall / (precision + recall + 1.e-8)) * 100

    return stats

