# Detect and remove duplicates from Immich library.

## How to use
```
python3 -m pip install -r ./requirements.txt
cd src
python3 main.py
```

optional arguments:
```
  -h, --help            show this help message and exit
  -v, --verbose         Enable verbose
  -d, --dry-run         Only create the result file, don't run the deletion process
  -l, --delete-only     Only run the deletion process, from an already existing result file
  -r, --restart         Clear hashes cache
  -s SIMILARITY, --similarity SIMILARITY
                        define similarity percentage threshold (default is 95)
```

If you change the similarity, you must use `r`to recompute all hashes. Otherwise, there is a cache mecanism that can be convient if your library is very big and you want to stop the process and not restart from scratch.