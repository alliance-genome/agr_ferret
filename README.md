[![Build Status](https://travis-ci.org/alliance-genome/agr_ferret.svg?branch=master)](https://travis-ci.org/alliance-genome/agr_ferret)
# agr_ferret
pre-ETL data fetching software for the Alliance of Genome Resources.

## Background
The Alliance of Genome Resources "ferret" is designed to parse through a series of YAML files, download datasets listed within those files, and subsequently upload them to the Alliance of Genome Features file management software ("chipmunk").

## Use

From the `src` directory: `python app.py`

Optional flags:
-  `-v` `--verbose`: Enable verbose mode. This mode can also be set by declaring the environmental variable `DEBUG=True`.
-  `-f` `--files`:  Specify the specific filenames to be parsed for datasets. By default, when this flag is **not** used, every YAML file in the `datasets` directory is parsed. Individual files can be specified with this flag. Wildcards are also supported:
    -  _e.g._ `python app.py -f datasets/MOD_FlyBase.yaml`
    -  _e.g._ `python app.py -f datasets/MOD*`

## Additional Information

- YAML files in the `datasets` folder are grouped by data provider. For example, the `MOD_FlyBase.yaml` file contains all datasets provided by FlyBase as a list. 
- When adding new values for YAML `ids` (the value at the very top of each YAML dataset file), `compression`, `data types`, or `data subtypes`, be sure to edit the validation file in `src/validation/validation.yaml` to allow these entries.
- Downloaded files are stored in the `files` folder. Files from previous runs are overwritten each time if the relevant dataset is processed.