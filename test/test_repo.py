import pytest

from promptgit.repo import PromptRepo

TEST_REPO = '/workspace/promptstore'

@pytest.fixture
def repo():
    return PromptRepo(TEST_REPO)

def test_main(repo):
    assert repo('test') == 'Hi. How are you doing?'

def test_pirate(repo):
    prompt = repo('pirates/first')
    assert prompt == "Answer question in pirate voice.\nQuestion: {question}\nAnswer:"
