import os
import pytest

from promptgit.repo import PromptRepo

TEST_REPO = '/workspace/promptest'
REMOTE = 'https://github.com/tvaroska/promptest.git'

# TODO: test as non-git !!!

@pytest.fixture
def repo():
    location = os.getenv('PROMPT_REPO')
    if not location:
        location = TEST_REPO
    return PromptRepo(location)

def test_main(repo):
    assert repo('test') == 'Hi. How are you doing?'

def test_pirate(repo):
    prompt = repo('pirates/first')
    assert prompt == "Answer question in pirate voice.\nQuestion: {question}\nAnswer:"

def test_changes(repo):

    changes = repo.list_changes()

    assert changes[0].name == 'first'
    assert changes[1].name == 'second'

def test_remote():
    repo = PromptRepo(REMOTE)

    assert repo('test') == 'Hi. How are you doing?'

def test_subdir():
    repo = PromptRepo(TEST_REPO, dir='questions')
    with pytest.raises(KeyError) as exec_info:
        assert repo('test') == 'Hi. How are you doing?'
    assert isinstance(exec_info.value, KeyError)

    prompt = repo('pirates/first')
    assert prompt == "Answer question in pirate voice.\nQuestion: {question}\nAnswer:"
