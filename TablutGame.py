from Utils import Entity, State, LastMoves
from copy import deepcopy
import random
from time import sleep
import pygame 
from Utils import CELL_SIZE
import datetime, os
from AI.ReadyDataset import state_to_nparray, initialize_nps
import numpy as np

class NeuralNet:

    def __init__(self) -> None:
        from tensorflow.keras.models import load_model
        self.model = load_model(r"AI\SavedModels\model_last3") 
        self.np_camps, self.np_castle, self.np_escapes = initialize_nps()
        
        # Warm up
        test_matrix = np.expand_dims(np.ones((self.model.input_shape[1:])), axis=0)
        self.model.predict(test_matrix)

    def get_state_score(self, state):
        np_mat = state_to_nparray(self.np_camps, self.np_castle, self.np_escapes, state=state)
        np_mat = np.expand_dims(np_mat, axis=0)
        np_mat = np.transpose(np_mat, (0, 2, 3, 1))
        # np_mat = np_mat.reshape((np_mat.shape[0], np_mat.shape[2], np_mat.shape[3], np_mat.shape[1]))
        return self.model.predict(np_mat)[0][0]


class TablutGame:
    initial_state = [
    ['O', '*', '*', 'B', 'B', 'B', '*', '*', 'O'],
    ['*', 'O', 'O', 'O', 'B', 'O', 'O', 'O', '*'],
    ['*', 'O', 'O', 'O', 'W', 'O', 'O', 'O', '*'],
    ['B', 'O', 'O', 'O', 'W', 'O', 'O', 'O', 'B'],
    ['B', 'B', 'W', 'W', 'K', 'W', 'W', 'B', 'B'],
    ['B', 'O', 'O', 'O', 'W', 'O', 'O', 'O', 'B'],
    ['*', 'O', 'O', 'O', 'W', 'O', 'O', 'O', '*'],
    ['*', 'O', 'O', 'O', 'B', 'O', 'O', 'O', '*'],
    ['O', '*', '*', 'B', 'B', 'B', '*', '*', 'O']
    ]

    def __init__(self, w_play_mode, b_play_mode) -> None:
        """
        Initialize the Tablut game and Pygame for visualization.
        """
        self.w_play_mode , self.b_play_mode = w_play_mode, b_play_mode
        play_mode_functions = {
            PlayMode.user : self.user_play,
            PlayMode.random : self.random_play,
            PlayMode.next_best_nn: self.neural_net,
        }
        self.w_play_function = play_mode_functions[w_play_mode]
        self.b_play_function = play_mode_functions[b_play_mode]
        if self.w_play_function == self.neural_net or self.b_play_function == self.neural_net:
            self.nn_engine = NeuralNet()

        self.records = []
        self.state = State(TablutGame.initial_state, last_move=LastMoves.initial_state)
        self.board_size = len(self.state.board)
        self.game_finished = False
        self.selected_piece = None
        self.current_player = Entity.white
        self.winner = None

        # Initialize Pygame
        pygame.init()
        self.cell_size = CELL_SIZE
        # Set up the Pygame window
        self.screen = pygame.display.set_mode((CELL_SIZE*self.board_size, CELL_SIZE*self.board_size + 50))
        self.screen.fill((255, 255, 255))
        pygame.display.set_caption("Tablut Game")

    def __random_move(self, for_player) -> tuple:
        """
        Generate a random move for the specified player.
        Args:
            for_player: The player for whom the move is generated.
        Returns:
            A tuple representing the move indexes (i, j, new_i, new_j).
        """
        possible_moves = self.state.possible_moves(for_player=for_player)
        return random.choice(possible_moves)

    def save_game_log(self):
        string = ""
        for state in self.records:
            string += f"moved_by: {state.last_move}\n"
            # Convert the 2D array into a string
            board_str = '\n'.join([''.join(row) for row in state.board])
            # Replace '*' and '+' and '0' with 'O'
            board_str = board_str.replace('*', 'O').replace('+', 'O').replace('0', 'O')
            string += board_str
            string += "\n-\n"
        string += f"winner: {self.winner}"

        # Get the current timestamp
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        # Define the filename with the timestamp
        save_dir = r"AI\GameRecords"
        os.makedirs(save_dir, exist_ok=True)
        filename = f"{self.winner}_{timestamp}_{str(len(self.records))}_b{self.b_play_mode[0]}_w{self.w_play_mode[0]}.txt"
        # Convert the string and save it to the file
        with open(os.path.join(save_dir, filename), "w") as file:
            file.write(string)


    def run_visualization(self):
        """
        Run the Pygame visualization of the game board.
        """
        self.state.pygame_visualize(self.screen)


    def check_if_move_captures(self, i, j):
        """
        Check for piece captures in multiple directions based on the last move.
        Args:
            i: Row index of the moved piece.
            j: Column index of the moved piece.
        This function checks for piece captures in four directions (right, left, down, up). 
        It updates the board based on the last player's move and captured pieces.
        """
        possible_directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        if self.current_player == LastMoves.white:
            invalid_squares_for_capture = [Entity.square, Entity.escape, Entity.camp]
            capture_with_help_of = [Entity.castle, Entity.king, Entity.white]
        elif self.current_player == LastMoves.black:
            invalid_squares_for_capture = [Entity.square, Entity.escape, Entity.king]
            capture_with_help_of = [Entity.black, Entity.camp]

        for rl, ud in possible_directions:
            counter = 0
            passed_squares = []
            while True:
                counter += 1
                new_i = i + counter*ud  
                new_j = j + counter*rl
                if not self.state.check_if_index_is_inside_board(new_i, new_j): break
                if self.state.board[new_i][new_j] in invalid_squares_for_capture: 
                    break
                
                elif self.state.board[new_i][new_j] in capture_with_help_of:
                    for sq in passed_squares:
                        col, row = sq
                        self.state.board[col][row] = State().board[col][row]
                    break
                
                passed_squares.append((new_i, new_j))


    def game_over(self, winner=None):
        self.records.append(self.state)
        if not winner:
            print("Draw")
            self.winner = 'D'
        elif winner == Entity.black:
            print("Black Wins")
            self.winner = Entity.black
        elif winner == Entity.white:
            self.winner = Entity.white
            print("White wins.")
        self.game_finished = True
        self.save_game_log()


    def who_is_opponent_of(self, player):
        if player == Entity.white or player == Entity.king:
            return Entity.black 
        if player == Entity.black: 
            return Entity.white 
        
    def change_player_turn(self):
        self.current_player = self.who_is_opponent_of(self.current_player)
    
    def update_board(self, move_indexes:tuple):
        """
        Update the game board with the specified move.

        Args:
            move_indexes: A tuple representing the move indexes (i, j, new_i, new_j).
            moved_by: The player who made the move.
        """
        i, j, new_i, new_j = move_indexes
        new_state = deepcopy(self.state.board)
        new_state[new_i][new_j] = new_state[i][j]
        new_state[i][j] = State().board[i][j] 
        
        # update current state and add the last state to the list of records
        self.records.append(self.state)
        self.state = State(new_state, last_move=self.current_player)
        self.check_if_move_captures(new_i, new_j)
        self.check_game_has_winner(new_i, new_j)
        self.change_player_turn()


    def if_black_captured_king(self, i, j):
        if self.current_player == LastMoves.black:
            if self.if_king_captured(i, j): return True
        return False
    
    def if_king_escaped(self, i, j):
        if self.current_player == LastMoves.white:
            if self.state.board[i][j] == Entity.king and State().board[i][j] == Entity.escape:
                    return True
        return False
    
    def if_next_player_can_move(self):
        who_plays_next = self.who_is_opponent_of(self.current_player)
        possible_moves_for_next_player = self.state.possible_moves(who_plays_next)
        if not possible_moves_for_next_player:
            return False 
        return True

    def check_game_has_winner(self, i, j):
        if self.if_black_captured_king(i, j): self.game_over(Entity.black)
        if self.if_king_escaped(i, j): self.game_over(Entity.white)
        if not self.if_next_player_can_move(): self.game_over(self.current_player)

    def if_king_captured(self, c_i, c_j):
        for i in range(self.board_size):
            for j in range(self.board_size):
                if self.state.board[i][j] == Entity.king:
                  king_location = (i,j)
                  break
        center = (self.board_size - 1) // 2  # Calculate the center square
        if king_location == (center, center):
            # King is in the center square, check if it's surrounded by black pieces
            center_neighbors = [(center - 1, center), (center + 1, center), (center, center - 1), (center, center + 1)]
            for i, j in center_neighbors:
                if self.state.board[i][j] != Entity.black:
                    return False  # King is not surrounded on all four sides
            return True  # King is surrounded by black pieces
        
        center_neighbors = [(center - 1, center), (center + 1, center), (center, center - 1), (center, center + 1)]
        if king_location in center_neighbors:
            ## king is near the castle, it must be surrounded by three black pieces and the castle
            k_i, k_j = king_location
            king_neighbors = [(k_i,k_j+1), (k_i,k_j-1), (k_i+1,k_j), (k_i-1,k_j)]
            for i, j in king_neighbors:
                if self.state.board[i][j] not in (Entity.black, Entity.castle):
                    return False 
            return True
        
        possible_directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        for rl, ud in possible_directions:
            new_i = c_i + ud  
            new_j = c_j + rl
            try:
                if self.state.board[new_i][new_j] == Entity.king:
                    new_i = c_i + 2*ud  
                    new_j = c_j + 2*rl
                    if self.state.board[new_i][new_j] == Entity.black:
                        return True
                    break
            except IndexError: return False


    def white_move(self):
        self.w_play_function()

    def black_move(self):
        self.b_play_function()

    def neural_net(self):
        possible_moves = self.state.possible_moves(self.current_player)
        possible_states = []
        for move_indexes in possible_moves:
            i, j, new_i, new_j = move_indexes
            new_board = deepcopy(self.state.board)
            new_board[new_i][new_j] = new_board[i][j]
            new_board[i][j] = State().board[i][j] 
            
            new_state = State(new_board, last_move=self.current_player)
            new_state.score =self.nn_engine.get_state_score(new_state)
            # for i in range(self.board_size):
            #     for j in range(self.board_size):
            #         if new_state.board[i][j] == Entity.king and State().board[i][j] == Entity.escape:
            #             new_state.score = 100
            
            possible_states.append(new_state)
        
        if self.current_player == Entity.white:
            index_of_state = max(enumerate(possible_states), key=lambda x: x[1].score)[0]
        elif self.current_player == Entity.black:
            index_of_state = min(enumerate(possible_states), key=lambda x: x[1].score)[0]
        self.update_board(possible_moves[index_of_state])
        print(possible_states[index_of_state].score)


    def random_play(self):
        # play a random move
        self.update_board(self.__random_move(self.current_player))

    def user_play(self):
        # wait for user to play
        def draw_rect_alpha(surface, color, rect):
            shape_surf = pygame.Surface(pygame.Rect(rect).size, pygame.SRCALPHA)
            pygame.draw.rect(shape_surf, color, shape_surf.get_rect())
            surface.blit(shape_surf, rect)
        for event in pygame.event.get():
            if event.type == pygame.MOUSEBUTTONDOWN:
                x, y = pygame.mouse.get_pos()
                i, j = y // self.cell_size, x // self.cell_size
                # If a square is clicked and no piece is selected, select the piece
                if self.selected_piece is None \
                    and self.state.board[i][j] in [Entity.white, Entity.black, Entity.king]:
                    # white can only select white, black can only select black
                    if self.state.board[i][j] == self.current_player \
                    or (self.state.board[i][j] == Entity.king and self.current_player == Entity.white):
                        self.selected_piece = (i, j)
                # If a piece is already selected, move it
                elif self.selected_piece is not None:
                    if (i,j) not in self.selected_piece_possible_moves or (i,j) == self.selected_piece:
                        self.selected_piece = None 
                        self.selected_piece_possible_moves = None
                        continue
                    move_indexes = self.selected_piece + (i, j)
                    self.update_board(move_indexes)
                    self.selected_piece = None

        # Draw the selected square with a color fill (e.g., semi-transparent red)
        if self.selected_piece is not None:
            i, j = self.selected_piece
            draw_rect_alpha(self.screen, (255, 0, 0, 127), (j * CELL_SIZE, i * CELL_SIZE, CELL_SIZE, CELL_SIZE))
            self.selected_piece_possible_moves = self.state.possible_moves_for_index(i, j)
            for (i_, j_) in self.selected_piece_possible_moves:
                draw_rect_alpha(self.screen, (0, 255, 0, 127), (j_ * CELL_SIZE, i_ * CELL_SIZE, CELL_SIZE, CELL_SIZE))

    def play(self):
        sleep(0.001)
        self.run_visualization()
        if self.current_player == Entity.white:
            self.white_move() 
        elif self.current_player == Entity.black:
            self.black_move()
        pygame.display.flip()


class PlayMode:   
    user = 0,
    random = 1,
    next_best_nn = 2,

if __name__=="__main__":
    while True:
        RandomPlaySleep = 1
        game = TablutGame(w_play_mode=PlayMode.random, b_play_mode=PlayMode.next_best_nn)
        while not game.game_finished:
            game.play()
        pygame.quit()