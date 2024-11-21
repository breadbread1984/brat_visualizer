# Introduction

this project provides a visualizer for brat annotation file

# Usage

## Install prerequisite

```shell
python3 -m pip install -r requirements.txt
```

## load brat annotation input neo4j database

```shell
python3 load.py --input <path/to/annotation/file> --host <neo4j/host> --user <neo4j/user> --password <neo4j/password> --database <neo4j/database>
```
