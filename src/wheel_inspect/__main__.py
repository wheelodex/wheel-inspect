import json
import os.path
import sys
from   .inspecting import inspect_dist_info_dir, inspect_wheel

def main():
    for path in sys.argv[1:]:
        if os.path.isdir(path):
            about = inspect_dist_info_dir(path)
        else:
            about = inspect_wheel(path)
        print(json.dumps(about, sort_keys=True, indent=4))

if __name__ == '__main__':
    main()
