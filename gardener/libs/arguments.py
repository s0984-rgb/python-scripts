import argparse
import re

age_regex_str = r'[smhdwM]'
size_regex_str = r'[KMGT]?B'

def compound_regex(regex):
    return '^[0-9]*[ ]?' + regex + '$'

def age_regex(arg_value, pat=compound_regex(age_regex_str)):
    pattern=re.compile(pat)
    if not pattern.match(arg_value):
        raise argparse.ArgumentTypeError('invalid value. regex format: {s}'.format(s=pat))
    return arg_value

def size_regex(arg_value, pat=compound_regex(size_regex_str)):
    pattern=re.compile(pat)
    if not pattern.match(arg_value.upper()):
        raise argparse.ArgumentTypeError('invalid value. regex format: {s}'.format(s=pat))
    return arg_value

parser = argparse.ArgumentParser(prog='python gardener.py', description='Deletes all files matching the \'file_patter\' in the \'path\' provided as keys in the JSON array. Logs all files deleted in ./logs/gardener.logs')
parser.add_argument('--system', '-s', help='System generating the recurring files. Translates to root keys in the JSON array.', default='All', type=str)
parser.add_argument('--config', '-c', help="Configuration file for the script in JSON array format. Needs a root key defined in argument --system. With keys 'path' and 'file_pattern'. e.g.: \n '{\'a\': {\'path\': \'/path/to/folder/a\', \'file_pattern\': \'*.log\'}, \'b\': {\'path\': \'/path/to/folder/b\', \'file_pattern\': \'*.txt\'}}'", default='settings.json', type=str)
parser.add_argument('--enable_file_logging', '-l', help='Program will log to a file', action='store_true')
parser.add_argument('--age', '-a', help='Change default mtime parameter (e.g. \'1m\' for 1 minute). Defaults = 1d', default='1d', type=age_regex)
parser.add_argument('--debug', '-d', help='Change default logging to debug', action='store_true')
parser.add_argument('--disable_logging', help='Prevent script from logging at all', action='store_true')
parser.add_argument('--min_size', '-m', help='Minimum file size to delete', default='10G', type=size_regex)

args = parser.parse_args()
