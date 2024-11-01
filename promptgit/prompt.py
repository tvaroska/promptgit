"""
    Core prompt object

"""

import json
import string
import yaml

from typing import Dict, List, Optional, Union, NamedTuple
from pathlib import Path
from pydantic import BaseModel, field_validator, model_validator


MULTI_LINE = ["prmpt", "description"]


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


def parse_md(text: str) -> Dict:
    current_section = None
    content = {}

    def safe_add(data, key, line):
        if key in data:
            if isinstance(data[key], str):
                data[key] = data[key] + "\n" + line
            elif isinstance(data[key], list):
                data[key].append(line)
            else:
                raise NotImplementedError
        else:
            if key in "models":
                data[key] = [line]
            else:
                data[key] = line
        return data

    def standardize_sections(key: str) -> str:
        return (
            key.replace("#", "")
            .strip()
            .lower()
            .replace(" ", "_")
            .replace("-", "_")
        )

    for line in text.splitlines():
        if line.strip() == "":
            if current_section and current_section in MULTI_LINE:
                content = safe_add(content, current_section, line)
                continue
            else:
                continue
        if line[0] == "#":
            current_section = standardize_sections(line)
            continue
        if not current_section:
            current_section = "prompt"
        if current_section in content:
            content[current_section] = content[current_section] + "\n" + line
        else:
            content[current_section] = line

    return content


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

    prompt: str
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
        for _, var, _, _ in string.Formatter().parse(self.prompt):
            if var is not None and var not in variables:
                variables.append(var)
        
        self.variables = variables if variables else None
        
        return self

    @classmethod
    def from_text(cls, content: str):
        return cls(prompt = content)

    @classmethod
    def from_json(cls, content: str):
        return cls(**json.loads(content))

    @classmethod
    def from_yaml(cls, content: str):
        return cls(**yaml.load(content))

    @classmethod
    def from_md(cls, content: str):
        current_section = None
        fields = {}

        def safe_add(data, key, line):
            if key in data:
                if isinstance(data[key], str):
                    data[key] = data[key] + "\n" + line
                elif isinstance(data[key], list):
                    data[key].append(line)
                else:
                    raise NotImplementedError
            else:
                if key in "models":
                    data[key] = [line]
                else:
                    data[key] = line
            return data

        def standardize_sections(key: str) -> str:
            return (
                key.replace("#", "")
                .strip()
                .lower()
                .replace(" ", "_")
                .replace("-", "_")
            )

        for line in content.splitlines():
            if line.strip() == "":
                if current_section and current_section in MULTI_LINE:
                    fields = safe_add(fields, current_section, line)
                    continue
                else:
                    continue
            if line[0] == "#":
                current_section = standardize_sections(line)
                continue
            if not current_section:
                current_section = "prompt"
            if current_section in fields:
                fields[current_section] = fields[current_section] + "\n" + line
            else:
                fields[current_section] = line

        return cls(**fields)


    def as_langchain(self):
        try:
            from langchain_core.prompts import PromptTemplate
        except ModuleNotFoundError:
            raise ModuleNotFoundError('Install promptgit[langchain] to use with langchain prompts')

        return PromptTemplate.from_template(self.prompt)

    def __str__(self):
        return self.prompt

    @property
    def location(self):
        return PromptLocation(application=self.application, name=self.name)
