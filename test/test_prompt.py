import json

import pytest

from promptgit import Prompt
from promptgit.prompt import parse_json, parse_md


@pytest.mark.parametrize("text", ["Hi", "How are you?"])
def test_text(text: str):
    assert Prompt(prompt=text).prompt == text
    assert Prompt.from_text(text).prompt == text


JSON_TESTS = [
    {"prompt": "Hi", "application": "first", "use_case": "q&a"},
    {"prompt": "Empty"},
    {"prompt": "Hi", "priority": 0}
]


@pytest.mark.parametrize("data", JSON_TESTS)
def test_json(data):
    prompt = Prompt.from_text(json.dumps(data), parser=parse_json)

    for key in data.keys():
        if key in dir(prompt):
            assert getattr(prompt, key) == data[key]


MD_TESTS = [
    "# Prompt\nHi. How are you doing?\n# Application\ndebugger\n \n# Description\nJust a stupid test\n# Use Case\ncreative",
]


@pytest.mark.parametrize("data", MD_TESTS)
def test_md(data):
    prompt = Prompt.from_text(data, parser=parse_md)

    assert prompt.prompt == "Hi. How are you doing?"
    assert prompt.description == "Just a stupid test"
    assert prompt.application == "debugger"
    assert prompt.use_case == "creative"

def test_from_text_variables():
    prompt = Prompt.from_text('You are an executive assistant to {user}. The tasks are {tasks}')

    assert prompt.variables == ['user', 'tasks']

def test_direct_variables():
    prompt = Prompt(prompt='You are an executive assistant to {user}. The tasks are {tasks}')

    assert prompt.variables == ['user', 'tasks']