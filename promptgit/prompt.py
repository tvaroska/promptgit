"""
    Core prompt object

"""

import string
import yaml

from typing import Dict, List, Optional, Union, NamedTuple, Literal
from pathlib import Path
from pydantic import BaseModel, field_validator, model_validator

import mistletoe
from mistletoe.block_token import Heading, Paragraph
from mistletoe.span_token import LineBreak

class PromptLocation(NamedTuple):
    """
    'Location' of a prompt
    application/prompt name
    """

    application: str
    name: str

    @classmethod
    def from_dir(cls, path):
        p = Path(path)

        return cls(
            application=p.parts[-2] if len(p.parts) > 1 else None, name=p.stem
        )

    @classmethod
    def from_str(cls, location):
        splits = location.split("/")
        if len(splits) == 1:
            application = None
            name = location
        elif len(splits) == 2:
            application = splits[0]
            name = splits[1]
        else:
            raise ValueError

        return cls(application=application, name=name)

    def __str__(self):
        if self.application:
            return f"{self.application}/{self.name}"
        else:
            return f"{self.name}"

class PromptTurn(BaseModel):
    role: Literal['system', 'user', 'human', 'model', 'ai']
    content: str

class Prompt(BaseModel):
    """Core prompt object

    Parameters:
        prompt (str): content of the prompt
        application (str) and name (str) : defines adress of the prompt in repo
        models (str or list of str): acceptable models for prompt
        description (str): description of prompt
        use_case (str): High level use case, for example summarization, qan
        variables (list): List of variable names (str for now)
    """

    prompt: Union[str, List[PromptTurn]]
    application: Optional[str] = None
    name: Optional[str] = None
    models: Union[str, List[str]] = []
    description: Optional[str] = None
    use_case: Optional[str] = None
    variables: Optional[List[str]] = None

    @field_validator("models")
    @classmethod
    def convert_single(cls, models: Union[str, List[str]]) -> List[str]:
        if isinstance(models, str):
            return [models]
        else:
            return models

    @model_validator(mode='after')
    def parse_variables(self) -> 'Prompt':
        """Parse variables from the prompt template and store them in variables property"""
        # Get all variables from the prompt using string.Formatter
        # Preserve order of appearance in the prompt
        variables = []
        if isinstance(self.prompt, str):
            prompts = [self.prompt]
        else:
            prompts = [turn.content for turn in self.prompt]
        for prompt in prompts:
            for _, var, _, _ in string.Formatter().parse(prompt):
                if var is not None and var not in variables:
                    variables.append(var)
        
        self.variables = variables if variables else None
        
        return self

    @classmethod
    def from_text(cls, content: str):
        return cls(prompt = content)

    @classmethod
    def from_json(cls, content: str):
        return cls.model_validate_json(content)

    @classmethod
    def from_yaml(cls, content: str):
        return cls.model_validate(yaml.safe_load(content))

    @classmethod
    def from_md(cls, content: str):

        def parse_children(children):

            max_level = min([item.level for item in children if isinstance(item, Heading)])

            top_level = [(item, idx) for (idx, item) in enumerate(children) if isinstance(item, Heading) and item.level == max_level]

            response = {}
  
            for i, (heading, idx) in enumerate(top_level):
                if isinstance(children[idx+1], Paragraph):
                    content = ''
                    for child in children[idx+1].children:
                        if isinstance(child, LineBreak):
                            content += '\n'
                        else:
                            try:
                                content += child.content
                            except AttributeError:
                                pass
                else:
                    print(f'{idx+1} - {top_level[i+1][1]}')
                    content = parse_children(children[idx+1:top_level[i+1][1]])
                response[heading.children[0].content.strip().lower().replace(" ", "_").replace("-", "_")] = content
    
            return response

        fields = parse_children(mistletoe.Document(content).children)
        # Multiple models - each one at one line
        if 'models' in fields:
            fields['models'] = fields['models'].split('\n')

        return cls.model_validate(fields)


    def as_langchain(self):
        try:
            from langchain_core.prompts import PromptTemplate, ChatPromptTemplate
        except ModuleNotFoundError:
            raise ModuleNotFoundError('Install promptgit[langchain] to use with langchain prompts')

        if isinstance(self.prompt, str):
            return PromptTemplate(template=self.prompt, template_format='f-string', input_variables=self.variables)
        else:
            return ChatPromptTemplate(
                template = [(item.role, item.content) for item in self.prompt],
                template_format='f-string',
                input_variables=self.variables
            )

    def __str__(self):
        if isinstance(self.prompt, str):
            return self.prompt
        else:
            return '['+','.join([item.json() for item in self.prompt])+']'

    @property
    def location(self):
        return PromptLocation(application=self.application, name=self.name)
