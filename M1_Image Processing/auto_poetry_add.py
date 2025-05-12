import ast
import json
import subprocess
import sys
from pathlib import Path
import importlib.util
import argparse

# List of standard library modules for Python 3.10
# For a comprehensive list, consider using 'stdlib-list' package
STANDARD_LIBS = {
    'abc', 'argparse', 'array', 'asyncio', 'base64', 'binascii', 'bisect',
    'builtins', 'calendar', 'collections', 'concurrent', 'contextlib',
    'copy', 'csv', 'datetime', 'decimal', 'difflib', 'dis', 'email', 'enum',
    'errno', 'faulthandler', 'fnmatch', 'functools', 'gc', 'getopt',
    'getpass', 'gettext', 'glob', 'gzip', 'hashlib', 'heapq', 'hmac',
    'html', 'http', 'imaplib', 'imp', 'importlib', 'inspect', 'io', 'itertools',
    'json', 'logging', 'lzma', 'math', 'multiprocessing', 'numbers', 'operator',
    'os', 'pathlib', 'pickle', 'platform', 'plistlib', 'pprint', 'queue',
    'random', 're', 'sched', 'secrets', 'select', 'selectors', 'shlex',
    'shutil', 'signal', 'socket', 'sqlite3', 'ssl', 'stat', 'statistics',
    'string', 'stringprep', 'struct', 'subprocess', 'sys', 'sysconfig',
    'tempfile', 'textwrap', 'threading', 'time', 'timeit', 'traceback',
    'types', 'typing', 'unittest', 'urllib', 'uuid', 'warnings', 'wave',
    'weakref', 'webbrowser', 'xml', 'zipfile', 'zipimport', 'zlib'
}

def extract_imports_from_py(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        node = ast.parse(f.read(), filename=file_path)
    imports = set()
    for n in ast.walk(node):
        if isinstance(n, ast.Import):
            for alias in n.names:
                imports.add(alias.name.split('.')[0])
        elif isinstance(n, ast.ImportFrom):
            if n.module:
                imports.add(n.module.split('.')[0])
    return imports

def extract_imports_from_ipynb(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        notebook = json.load(f)
    imports = set()
    for cell in notebook.get('cells', []):
        if cell.get('cell_type') == 'code':
            source = ''.join(cell.get('source', []))
            try:
                node = ast.parse(source)
                for n in ast.walk(node):
                    if isinstance(n, ast.Import):
                        for alias in n.names:
                            imports.add(alias.name.split('.')[0])
                    elif isinstance(n, ast.ImportFrom):
                        if n.module:
                            imports.add(n.module.split('.')[0])
            except SyntaxError:
                continue
    return imports

def is_standard_lib(module_name):
    return module_name in STANDARD_LIBS

def is_installed(module_name):
    spec = importlib.util.find_spec(module_name)
    return spec is not None

def add_with_poetry(package_name):
    try:
        subprocess.run(['poetry', 'add', package_name], check=True)
    except subprocess.CalledProcessError:
        print(f"Failed to add {package_name} with Poetry.")

def main():
    parser = argparse.ArgumentParser(description='Automatically add missing imports to Poetry.')
    parser.add_argument('file', help='Path to the .py or .ipynb file')
    args = parser.parse_args()

    file_path = Path(args.file)
    if not file_path.exists():
        print(f"File {file_path} does not exist.")
        sys.exit(1)

    if file_path.suffix == '.py':
        imports = extract_imports_from_py(file_path)
    elif file_path.suffix == '.ipynb':
        imports = extract_imports_from_ipynb(file_path)
    else:
        print("Unsupported file type. Please provide a .py or .ipynb file.")
        sys.exit(1)

    for module in sorted(imports):
        if is_standard_lib(module):
            continue
        if is_installed(module):
            continue
        print(f"Adding {module} to Poetry dependencies...")
        add_with_poetry(module)

if __name__ == '__main__':
    main()
