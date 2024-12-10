"""

    promptgit package

    PropmtRepo: read whole repository and access individual prompts
        example:
            repo = PromptRepo(<location>)
            prompt = repo('main/test')

    Prompt: initial object to store prompts
        attributes:
            application
            name
            use_case
            description
            models

"""
from .repo import PromptRepo
from .prompt import Prompt

__version__ = '0.2.5'
__all__ = ['PromptRepo', 'FileTypes', 'Prompt']