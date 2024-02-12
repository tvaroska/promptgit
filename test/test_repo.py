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

def test_changes(repo):

    changes = repo.list_changes()

    assert changes[0].name == 'first'
    assert changes[1].name == 'second'