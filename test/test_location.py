import pytest

from pathlib import Path
from promptgit.prompt import PromptLocation

@pytest.mark.parametrize(
        ['filename', 'application', 'name'],
        [
            # Simple test
            ('/workspace/promptstore/test/first.txt', 'test', 'first'),
            # Only name
            ('test.md', None, 'test')
        ])
def test_from_dir(filename, application, name):

    # Test for string
    location = PromptLocation.from_dir(filename)

    assert location.application == application
    assert location.name == name

    # Test for Path
    location = PromptLocation.from_dir(Path(filename))

    assert location.application == application
    assert location.name == name


def test_from_str():

    t1 = PromptLocation.from_str('questions/first')
    assert t1.name == 'first'
    assert t1.application == 'questions'