# Promptgit

Library to manage prompts inside of git repo

## ProptRepo

Central object - open the repository

Prompts are organized on application/name structure. The structure can be infered from directory name (application) and filename (name) as default. Or it can be stored in the file itself.

Two options to access the prompts. Both will return pure string (prompt templates in the process)
### as dictionary
prompts['application/name']


### as object call
prompts('application/name')


### Open prompts from current (local directory)
prompts = promptgit.PromptRepo()

### Open prompts in 'prompts' subdirectory relative to current directory
prompts = promptgit.PromptRepo('prompts')

### Open directory from Pathlib object
prompts = promptgit.PromptRepo(pathlib.Path.cwd())

