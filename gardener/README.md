# Gardener
Gardener is a tool that helps you delete recurring files in your filesystem; keeping your filesystem clean.

## Why?
We've all come across those processes that can't stop logging.
Some sort of SDK that wasn't designed to be silenced, or a verbose process.

This scripts weeds out these files. It logs how many files were delete. Optionally, you can disable logging.

## Usage
You must first create a file that contains a JSON array. This JSON array contains root keys which contain a map of `path` and `file_pattern`.

This corresponds to the path the script must look through, for any file which matches the `file_pattern`.

See [settings.json.example](./settings.json.example) for an example

Once this is provided, run the script with the provided settings files. Optionally, you can tell the script to only delete files from 1 specific root key.

```bash
usage: python gardener.py [-h] [--system SYSTEM] [--config CONFIG] [--age AGE AGE] [--debug] [--disable_logging]

Deletes all files matching the 'file_patter' in the 'path' provided as keys in the JSON array. Logs all files deleted in ./logs/gardener.logs

options:
  -h, --help            show this help message and exit
  --system SYSTEM, -s SYSTEM
                        System generating the recurring files. Translates to root keys in the JSON array.
  --config CONFIG, -c CONFIG
                        Configuration file for the script in JSON array format. Needs a root key defined in argument --system. With keys 'path' and 'file_pattern'. e.g.: '{"a": {"path": "/path/to/folder/a", "file_pattern": "*.log"}, "b": {"path": "/path/to/folder/b", "file_pattern": "*.txt"}}'
  --age AGE AGE, -a AGE AGE
                        Change default mtime parameter (e.g. '1' 'm' for 1 minute). Defaults = 1 d
  --debug, -d           Change default logging to debug
  --disable_logging     Prevent script from logging at all
```
