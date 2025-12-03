Simple script to generate bingo cards with user inputs (number of players, number of winners, number of draws) as a printable PDF! 

Instructions

1. Create a `virtual environment` of choice or use the provided `.venv` (run `source .venv/bin/activate`)
2. Install requirements in venv: `pip install -r requirements.txt`
3. Run script with optional arguments
   ```python bingo_generator.py --participants <int> --rounds <int> --winners <int> --names "<name_1>,<name_2>,<name_3>,<name_4>"```

   Example: `python bingo_generator.py --participants 4 --rounds 2 --winners 1`
