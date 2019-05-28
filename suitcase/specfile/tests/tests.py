import json
import pytest
from suitcase.specfile import export, Serializer
from pkg_resources import resource_filename
from suitcase.utils.tests.conftest import one_stream_multi_descriptors_plan


# This test verifies that the specfiles generated by Serializer are exactly
# identical to the specfiles generated by bluesky's original specfile writer,
# previously shipped with the old, internal suitcase package in suitcase
# v0.7.0.

# The specfile writer only knows how to deal with counts, scans, and relative
# scans. Four representative plans were executed, and their documents were
# captured losslessly (as newline-delimited JSON). The documents were then read
# and re-serialized using the old specfile writer in suitcase v0.7.0. Those
# specfiles are stored in this repo under data_from_suitcase_v0.7.0/.

# This test loads those same losslessly-stored documents and uses Serializer to
# generate specfiles. It then compares these new specfiles to those in
# data_from_suitcase_v0.7.0, line by line.


@pytest.mark.parametrize('example', ['count_1', 'count_3', 'scan', 'rel_scan'])
def test_against_legacy_implementation(example, tmp_path):
    # Load example data from JSONL and re-serialize it as specfile.
    with Serializer(tmp_path, file_prefix=f'{example}') as serializer:
        jsonl_filename = resource_filename('suitcase.specfile',
                                           f'tests/documents/{example}.jsonl')
        with open(jsonl_filename) as f:
            for line in f:
                name, doc = json.loads(line)
                serializer(name, doc)
    spec_filename = resource_filename('suitcase.specfile',
                                      f'tests/data_from_suitcase_v0.7.0/{example}.spec')

    # Load specfile output and archival copies of expected specfile output.
    with open(spec_filename) as f:
        expected_lines = f.readlines()
    with open(tmp_path / f'{example}.spec') as f:
        actual_lines = f.readlines()
    assert actual_lines == expected_lines
    print("ACTUAL")
    print('\n'.join(actual_lines))
    print("EXPECTED")
    print('\n'.join(expected_lines))


def test_export(tmp_path, example_data):
    documents = example_data()
    try:
        export(documents, tmp_path)
    except NotImplementedError:
        raise pytest.skip()


def test_file_prefix_formatting(file_prefix_list, example_data, tmp_path):
    '''Runs a test of the ``file_prefix`` formatting.
    ..note::
        Due to the `file_prefix_list` and `example_data` `pytest.fixture`'s
        this will run multiple tests each with a range of file_prefixes,
        detectors and event_types. See `suitcase.utils.conftest` for more info.
    '''
    collector = example_data(ignore=[one_stream_multi_descriptors_plan])
    file_prefix = file_prefix_list()
    artifacts = export(collector, tmp_path, file_prefix=file_prefix)

    for name, doc in collector:
        if name == 'start':
            templated_file_prefix = file_prefix.format(
                start=doc).partition('-')[0]
            break

    if artifacts:
        unique_actual = set(str(artifact).split('/')[-1].partition('-')[0]
                            for artifact in artifacts['stream_data'])
        assert unique_actual == set([templated_file_prefix])
