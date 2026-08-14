---
title: Python Starter lesson-2
pubDate: '2022-08-24'
description: 'Python lesson 2: Package management and development setup'
tags: python
heroImage: '../../assets/blog-placeholder-1.jpg'
---

# Install
## why we use package manager
- 

### windows we choose scoop

```shell

Set-ExecutionPolicy RemoteSigned -Scope CurrentUser # Optional: Needed to run a remote script the first time

irm get.scoop.sh | iex

scoop bucket hexoadd versions

scoop install python310

python3 -V

```

### mac we choose brew

```shell

/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

brew install python

python3 -V

```


### for linux
- redhat -> yum
- debain -> apt-get
- suse -> yast2


# Redo what Hello python
- Python is a popular programming language and released in 1991.
- Now is Python3

#  start development

## how to use pip

```shell
pip3 install xxxxxx
```

## how to use IDE
### pycharm

- win
```shell
scoop install pycharm
```
- mac
```shell
brew install pycharm
```
### vscode

- win
```shell
scoop install vscode
```
- mac
```shell
brew install --cask visual-studio-code
```

- android
```shell
pkg install python
```


## read data from excel

- export a xlsx
```python
import pandas as pd
import random


COLUMNS = ('Man', 'Woman')

i = 0

score_list = []

while i < 100:
    score = (random.randint(10, 50), random.randint(24, 45))
    score_list.append(score)
    i += 1

df = pd.DataFrame(
    score_list,
    columns=COLUMNS
)

df.to_excel("test_data.xlsx", index=False, sheet_name='sheet_1')

#sheet2
score_list_2 = []

i = 0

while i < 10:
    score = (random.randint(10, 50), random.randint(24, 45))
    score_list_2.append(score)
    i += 1

df2 = pd.DataFrame(
    score_list_2,
    columns=COLUMNS
)

with pd.ExcelWriter('test_data.xlsx', mode='a') as writer:
    df2.to_excel(writer, index=False, sheet_name='sheet_2')

```

- read data from a xlsx

```python
import pandas as pd

data_1 = pd.read_excel('test_data.xlsx', sheet_name='sheet_1')

data_1.to_html('test_data_1.html')

data_2 = pd.read_excel('test_data.xlsx', sheet_name='sheet_2')

data_2.to_html('test_data_2.html')

for label, content in data_1.items():
    print('===================')
    print(f'label: {label}')
    print(f'content: {content}')


man_total = 0
woman_total = 0

for label, content in data_1.items():
    print('===================')
    print(f'sum-{label}:{content.sum()}')
    print(f'max-{label}:{content.max()}')
    print(f'min-{label}:{content.min()}')

```











