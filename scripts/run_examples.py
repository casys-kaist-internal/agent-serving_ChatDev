import subprocess
import os
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

WORK_DIR = os.getenv('WORK_DIR')
assert WORK_DIR is not None, "WORK_DIR environment variable not set"
assert 'ChatDev' not in WORK_DIR, f"Wrong directory setup, {WORK_DIR}"

games = [
    'Gomoku', 'Chess', 'Checkers', 'Connect Four', 'Tic Tac Toe', 'Backgammon', 'Othello', 'Battleship', 'Mancala', 'Pente',
    'Ludo', 'Snakes and Ladders', 'Nine Men\'s Morris', 'Chinese Checkers', 'Draughts',
    'Sudoku', 'Solitaire', 'Memory Game', 'Guess Who', 'Mastermind', 'Jenga',
    'Uno', 'Crazy Eights', 'War', 'Rummy', 'Gin Rummy', 'Euchre', 'Blackjack',
    'Hearts', 'Spades', 'Boggle', 'Yahtzee', 'Reversi', 'Dominoes', 'Go',
    'Qwirkle', 'Blokus', 'Sequence', 'Hive', 'Tsuro', 'The Game of Life',
    'Operation', 'Trouble', 'Sorry!', 'Aggravation', 'Taboo', 'Charades',
    'Apples to Apples', 'Sushi Go', 'Timeline', 'Spyfall', 'Sushi Go', 'Love Letter',
    'Coup', 'Skull', 'Kingdomino', 'Patchwork', 'Draftosaurus', 'Tokaido'
]

processes = []

def run_game_task(game):
    cmd = f"cd {WORK_DIR} && source .venv/bin/activate && python run.py --task 'Develop a basic {game} game.' --name {game}"
    subprocess.run(cmd, shell=True, text=True, executable="/bin/bash")

# try:
#     for game in games:
#         cmd = f"source .venv/bin/activate && python run.py --task 'Develop a basic {game} game.' --name {game}"
#         p = subprocess.Popen(
#             cmd,
#             text=True,
#             shell=True,
#             executable="/bin/bash",
#         )
#         processes.append(p)

#     for p in processes:
#         p.wait()

# except KeyboardInterrupt:
#     print("\nCaught Ctrl+C, terminating subprocesses...")
#     for p in processes:
#         p.terminate()  # 혹은 p.kill()
#     for p in processes:
#         p.wait()

if __name__ == "__main__":
    max_concurrent_processes = 10
    with ThreadPoolExecutor(max_workers=max_concurrent_processes) as executor:
        executor.map(run_game_task, games)
