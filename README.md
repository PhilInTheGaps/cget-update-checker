# cget-update-checker

This script can be used to see if there are updates available for `cget` dependencies specified in a `requirements.txt` file.
Note that currently only github dependencies are supported.

## Usage

```sh
python update-checker.py <requirements file>

example output:

frankosterfeld/qtkeychain: v0.13.2
taglib/taglib: v1.13
stachenov/quazip: v1.3 -> v1.4
```