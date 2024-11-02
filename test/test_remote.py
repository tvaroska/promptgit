from promptgit.repo import PromptRepo

REMOTE = 'https://github.com/tvaroska/promptest.git'


def test_remote():
    repo = PromptRepo(REMOTE)

    assert repo('test') == 'Hi. How are you doing?'
