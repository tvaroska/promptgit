import pytest

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

    location = PromptLocation.from_dir(filename)

    assert location.application == application
    assert location.name == name

def test_from_str():

    t1 = PromptLocation.from_str('questions/first')
    assert t1.name == 'first'
    assert t1.application == 'questions'