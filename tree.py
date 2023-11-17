from main import State, Entity
from copy import deepcopy
from random import choice 


class NeuralNetwork:
    def __init__(self, input_size, hidden_size, output_size) :
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.output_size = output_size


def initialize_board():
    return State.State

class TablutGameState:
    def __init__(self, board = None, player = Entity.white):
        self.board = board or initialize_board()
        self.player = player

    def terminal(self):
        if self.king_captured():
            print("Black wins!")
            return True
        
        if self.king_in_corner():
            print("White wins!")
            return True

        #Game_Over
        return False
    
    def king_position(self):
        for row_idx, row in enumerate(self.board):
            for col_idx, cell in enumerate(row):
                if cell == Entity.king:
                    return row_idx, col_idx
                
        return None
    
    def king_captured(self):
        #posithion of king
        king_position = self.king_position()

        if king_position is None:
            return False
        
        #king is surrounded by black
        row, col = king_position

        #above
        if row > 0 and self.board[row - 1][col] == Entity.black:
            return True
        #below
        if row < len(self.board) - 1 and self.board[row + 1][col] == Entity.black:
            return True
        #left
        if col > 0 and self.board[row][col - 1] == Entity.black:
            return True
        #right
        if col < len(self.board[0]) - 1 and self.board[row][col + 1] == Entity.black:
            return True

        return False

    def is_king_in_corner(self):
        #position of the king
        king_position = self.king_position()

        if king_position is None:
            return False
        
        row, col = king_position
        #king in squares
        return (row == 0 and col == 0) or \
               (row == 0 and col == len(self.board[0]) - 1) or \
               (row == len(self.board) - 1 and col == 0) or \
               (row == len(self.board) - 1 and col == len(self.board[0]) - 1)
    
    
    def generate_children(self):
        children = []
        for move in self.get_legal_moves():
            #create new child 
            
            child_state = self.apply_move(move)
            children.append(child_state)

        return children
    
    def get_legal_moves(self):
        legal_moves = []
        for row_idx, row in enumerate(self.board):
            for col_idx, cell in enumerate(row):
                if cell == self.player_turn:
                    legal_moves.extend(self.get_legal_moves_for_player(row_idx, col_idx))

        return legal_moves
    
    def get_legal_moves_for_player(self, row, col):
        legal_moves = []
        #above
        legal_moves.extend(self.get_legal_moves_in_direction(row, col, -1, 0))
        #below
        legal_moves.extend(self.get_legal_moves_in_direction(row, col, 1, 0))
        #left
        legal_moves.extend(self.get_legal_moves_in_direction(row, col, 0, -1))
        #right
        legal_moves.extend(self.get_legal_moves_in_direction(row, col, 0, 1))

        return legal_moves
    
    def get_legal_moves_in_direction(self, start_row, start_col, row_offset, col_offset):
        legal_moves = []
        current_row, current_col = start_row + row_offset, start_col + col_offset
        while 0 <= current_row < len(self.board) and 0 <= current_col < len(self.board[0]):
            if self.board[current_row][current_col] == [Entity.square, Entity.escape]:
                # Empty space is a legal move
                legal_moves.append((start_row, start_col, current_row, current_col))
                current_row += row_offset
                current_col += col_offset
            else:
                #It's occupied
                break

        return legal_moves
    
    def apply_move(self, move):
        start_row, start_col, end_row, end_col = move
        #current state
        new_board = [row[:] for row in self.board]
        new_state = TablutGameState(board=new_board, player_turn=self.player_turn)
        # Move the player
        new_state.board[end_row][end_col] = new_state.board[start_row][start_col]
        new_state.board[start_row][start_col] = [Entity.square, Entity.escape]  
        # Update the player turn
        new_state.player_turn = Entity.white if self.player_turn == Entity.black else Entity.black

        return new_state
    
    
    

   

    
#algorithm
class MinimaxSearchTree:
    def __init__(self, neural_network, depth):
        self.neural_network = neural_network
        self.depth = depth

    def search(self, node, maximizing_player=True, depth=None, alpha=float('-inf'), beta=float('inf')):
        if depth is None:
            depth = self.depth

        if depth == 0 or node.terminal():
            return self.neural_network.evaluate(node)

        if maximizing_player:
            max_eval = float('-inf')
            for child in node.generate_children():
                eval = self.search(child, False, depth - 1, alpha, beta)
                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)
                if beta <= alpha:
                    break  
            return max_eval
        else:
            min_eval = float('inf')
            for child in node.generate_children():
                eval = self.search(child, True, depth - 1, alpha, beta)
                min_eval = min(min_eval, eval)
                beta = min(beta, eval)
                if beta <= alpha:
                    break  
            return min_eval

    def best_move(self, node):
        best_move = None
        best_score = float('-inf')

        for child in node.generate_children():
            score = self.search(child, False)
            if score > best_score:
                best_score = score
                best_move = child.move

        return best_move

#test
neural_network = NeuralNetwork(input_size, hidden_size, output_size)
initial_state = TablutGameState()

search_tree = MinimaxSearchTree(neural_network, depth=3)
best_move = search_tree.best_move(initial_state)

print(best_move)











    