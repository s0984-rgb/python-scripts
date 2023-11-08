import argparse

parser = argparse.ArgumentParser(prog='python gardener.py', description="Deletes all files matching the 'file_patter' in the 'path' provided as keys in the JSON array. Logs all files deleted in ./logs/gardener.logs")
parser.add_argument('--system', '-s', help="System generating the recurring files. Translates to root keys in the JSON array.", default="All", type=str)
parser.add_argument('--config', '-c', help="Configuration file for the script in JSON array format. Needs a root key defined in argument --system. With keys 'path' and 'file_pattern'. e.g.: \n '{\"a\": {\"path\": \"/path/to/folder/a\", \"file_pattern\": \"*.log\"}, \"b\": {\"path\": \"/path/to/folder/b\", \"file_pattern\": \"*.txt\"}}'", default="settings.json", type=str)
parser.add_argument('--enable_file_logging', '-l', help="Program will log to a file", action='store_true')
parser.add_argument('--age', '-a', help="Change default mtime parameter (e.g. '1' 'm' for 1 minute). Defaults = 1 d", default="1" "d", type=str, nargs=2)
parser.add_argument('--debug', '-d', help="Change default logging to debug", action='store_true')
parser.add_argument('--disable_logging', help="Prevent script from logging at all", action='store_true')

args = parser.parse_args()
