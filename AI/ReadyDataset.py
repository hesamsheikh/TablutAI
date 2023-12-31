import os 
import numpy as np 
import sys 
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from Utils import State, Entity, score_function, LastMoves

class Record:
    def __init__(self, txt_path=None) -> None:
        self.states = []
        self.winner = None
        self.txt_path = txt_path

    def add_state(self, state:State):
        self.states.append(state)

def convert_dataset_txt_to_record(txt_path):
    with open(txt_path, 'r') as t:
        string_data = t.read()
    data_blocks = string_data.split('-\n')
    
    record = Record(txt_path)

    for db in data_blocks[:-1]:
        new_state = State()

        mvd_by = db.split("\n")[0]
        if mvd_by == "W":
            new_state.last_move = LastMoves.white
        elif mvd_by == "B":
            new_state.last_move = LastMoves.black
        elif mvd_by in ["BW", "WW"]: continue
        else:
            new_state.last_move = LastMoves.initial_state
        
        board_state_str = db.split("Stato:")[1]
        board_state = [list(a.strip()) for a in board_state_str.split("\n")]
        for r in board_state: 
            if not r:
                board_state.remove(r) 
        for i, row in enumerate(board_state):
            for j, sqr in enumerate(row):
                if sqr == 'W': new_state.board[i][j] = 'W'
                elif sqr == 'B': new_state.board[i][j] = 'B'
                elif sqr == 'K': new_state.board[i][j] = 'K'

        record.add_state(new_state)
    
    winner_state = data_blocks[-1].strip("\n")
    if winner_state == "WW":
        record.winner = Entity.white
    elif winner_state == "BW":
        record.winner = Entity.black
    elif winner_state == "D":
        record.winner = 'D'
    else:
        return
    
    # record.states[-1].visualize_board()
    return record

def calculate_score(record:Record):
    if record.winner == Entity.white:
        mul_factor = 1
    elif record.winner == Entity.black:
        mul_factor = -1 

    for i, state in enumerate(record.states):
        total_moves = len(record.states)
        state.score = mul_factor * score_function(i, 0, total_moves)

def compare_with_char(board_state, char):
    return (board_state == char).astype(int)
    
def initialize_nps():
    state = State()
    board_state = np.array(state.board)
    np_camps = compare_with_char(board_state, Entity.camp)
    np_castle = compare_with_char(board_state, Entity.castle)
    np_escapes = compare_with_char(board_state, Entity.escape)
    return np_camps, np_castle, np_escapes


def state_to_nparray(state:State):
    board_state = np.array(state.board)
    np_W = compare_with_char(board_state, "W")
    np_B = compare_with_char(board_state, "B")
    np_K = compare_with_char(board_state, "K") 
    output_matrix = np.stack((np_camps, np_castle, np_escapes, np_W, np_B, np_K), axis=0)
    return output_matrix

if __name__ == "__main__":
    dataset_path = r"AI\GameRecords"
    dataset_files = []
    for filename in os.listdir(dataset_path): 
        if filename.endswith("txt"):
            dataset_files.append(os.path.join(dataset_path, filename))

    records = []
    for df in dataset_files:
        data_record = convert_dataset_txt_to_record(df)
        if not data_record or data_record.winner == 'D': continue
        calculate_score(data_record)
        records.append(data_record)
        
    np_camps, np_castle, np_escapes = initialize_nps()

    Xs = []
    Ys = []
    for record in records:
        for state in record.states:
            Ys.append(state.score)
            state_matrix = state_to_nparray(state)
            Xs.append(state_matrix)

    Xs = np.array(Xs)
    Ys = np.array(Ys)

    np.save("X.npy" ,Xs)
    np.save("Y.npy", Ys)
    
    ...
import os 
import numpy as np 
import sys 
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from Utils import State, Entity, score_function, LastMoves, score_function_linear

class Record:
    def __init__(self, txt_path=None) -> None:
        self.states = []
        self.winner = None
        self.txt_path = txt_path

    def add_state(self, state:State):
        self.states.append(state)

def convert_dataset_txt_to_record(txt_path, self_play=False):
    with open(txt_path, 'r') as t:
        string_data = t.read()
    data_blocks = string_data.split('-\n')
    
    record = Record(txt_path)

    if not self_play:
        for db in data_blocks[:-1]:
            new_state = State()

            mvd_by = db.split("\n")[0]
            if mvd_by == "W":
                new_state.last_move = LastMoves.white
            elif mvd_by == "B":
                new_state.last_move = LastMoves.black
            elif mvd_by in ["BW", "WW"]: continue
            else:
                new_state.last_move = LastMoves.initial_state
            
            try:
                board_state_str = db.split("Stato:")[1]
            except IndexError:
                board_state_str = db.split("Stato:")[1]

            board_state = [list(a.strip()) for a in board_state_str.split("\n")]
            for r in board_state: 
                if not r:
                    board_state.remove(r) 
            for i, row in enumerate(board_state):
                for j, sqr in enumerate(row):
                    if sqr == 'W': new_state.board[i][j] = 'W'
                    elif sqr == 'B': new_state.board[i][j] = 'B'
                    elif sqr == 'K': new_state.board[i][j] = 'K'

            record.add_state(new_state)
        
        winner_state = data_blocks[-1].strip("\n")
        if winner_state == "WW":
            record.winner = Entity.white
        elif winner_state == "BW":
            record.winner = Entity.black
        elif winner_state == "D":
            record.winner = 'D'
        else:
            return
        
    ## For Self play
    else:
        for db in data_blocks[:-1]:
            new_state = State()

            mvd_by = db.split("\n")[0]
            mvd_by = mvd_by.replace("moved_by: ","")
            if mvd_by == "W":
                new_state.last_move = LastMoves.white
            elif mvd_by == "B":
                new_state.last_move = LastMoves.black
            elif mvd_by in ["BW", "WW"]: continue
            else:
                new_state.last_move = LastMoves.initial_state
            
            board_state_str = "\n".join(db.split("\n")[1:])[:-1]

            board_state = [list(a.strip()) for a in board_state_str.split("\n")]
            for r in board_state: 
                if not r:
                    board_state.remove(r) 
            for i, row in enumerate(board_state):
                for j, sqr in enumerate(row):
                    if sqr == 'W': new_state.board[i][j] = 'W'
                    elif sqr == 'B': new_state.board[i][j] = 'B'
                    elif sqr == 'K': new_state.board[i][j] = 'K'

            record.add_state(new_state)
        
        winner_state = data_blocks[-1][-1]
        if winner_state == "W":
            record.winner = Entity.white
        elif winner_state == "W":
            record.winner = Entity.black
        elif winner_state == "D":
            record.winner = 'D'
        else:
            return
        
    return record

def calculate_score(record:Record):
    if record.winner == Entity.white:
        mul_factor = 1
    elif record.winner == Entity.black:
        mul_factor = -1 

    for i, state in enumerate(record.states):
        total_moves = len(record.states)-1
        state.score = mul_factor * score_function_linear(i, total_moves)
    ...

def compare_with_char(board_state, char):
    return (board_state == char).astype(int)
    
def initialize_nps():
    state = State()
    board_state = np.array(state.board)
    np_camps = compare_with_char(board_state, Entity.camp)
    np_castle = compare_with_char(board_state, Entity.castle)
    np_escapes = compare_with_char(board_state, Entity.escape)
    return np_camps, np_castle, np_escapes


def state_to_nparray(np_camps, np_castle, np_escapes, state:State):
    board_state = np.array(state.board)
    np_W = compare_with_char(board_state, "W")
    np_B = compare_with_char(board_state, "B")
    np_K = compare_with_char(board_state, "K") 
    output_matrix = np.stack((np_camps, np_castle, np_escapes, np_W, np_B, np_K), axis=0)
    return output_matrix


def list_files(root_dir:str) -> list:
    """takes the path of a folder and returns all txt file paths in it"""
    txt_paths = []
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.endswith('txt'):
                txt_paths.append(os.path.join(root, file))
    return txt_paths

if __name__ == "__main__":
    np_camps, np_castle, np_escapes = initialize_nps()

    PreProvidedDatasetPath = r"AI\GameRecords\PreDataset"
    RecordsDatasetPath = r"AI\GameRecords\RecordsDataset"

    pre_dataset_files = list_files(PreProvidedDatasetPath)
    records_dataset_files = list_files(RecordsDatasetPath)


    records = []
    for df in pre_dataset_files:
        data_record = convert_dataset_txt_to_record(df, self_play=False)
        if not data_record or data_record.winner == 'D': continue
        calculate_score(data_record)
        records.append(data_record)

    for spf in records_dataset_files:
        data_record = convert_dataset_txt_to_record(spf, self_play=True)
        if not data_record or data_record.winner == 'D': continue
        calculate_score(data_record)
        records.append(data_record)

    Xs = []
    Ys = []
    for record in records:
        try:
            for state in record.states:
                Ys.append(state.score)
                state_matrix = state_to_nparray(np_camps, np_castle, np_escapes, state)
                Xs.append(state_matrix)
        except: pass 

    Xs = np.array(Xs)
    Ys = np.array(Ys)

    np.save(r"AI\NPYs\X.npy" ,Xs)
    np.save(r"AI\NPYs\Y.npy", Ys)
    
    ...