__version__ = "1.1.0"

import sys
import subprocess


def execute(cmd):
    process = subprocess.run(cmd,
                             capture_output=True,
                             # check=True,
                             universal_newlines=True)

    if process.stdout:
        print(process.stdout)
    
    if process.returncode != 0:
        print("Something went wrong. Consult the notes above.")
        print(process.stderr)

    process.check_returncode()


if __name__ == '__main__':
    execute([sys.executable, "-m", "pip", "install", "pymunk"])
