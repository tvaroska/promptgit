import pytest
from promptgit.repo import PromptRepo

REMOTE = 'https://github.com/tvaroska/promptest.git'


def test_remote():
    repo = PromptRepo(REMOTE)

    assert repo('test') == 'Hi. How are you doing?'

def test_tag_01():
    repo = PromptRepo(REMOTE, tag='0.1')

    assert repo('test') == 'Hi. How are you doing?'

    with pytest.raises(KeyError) as exc_info:   
        prompt = repo['pirates/first']
