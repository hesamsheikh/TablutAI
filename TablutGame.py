from Utils import Entity, State, LastMoves
from copy import deepcopy
import random
from time import sleep
import pygame 
from Utils import CELL_SIZE
import datetime, os
from NueralNetTFLite import NeuralNetTFLite
from Player import Agent


total_time_treeS = 0
tree_use_counterS = 0

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

    def __init__(self, w_play_mode, b_play_mode, save_game_log=False) -> None:
        """
        Initialize the Tablut game and Pygame for visualization.

        Initializes the Tablut game with specified playing modes for white and black players.
        Sets up Pygame for visual representation of the game.

        Args:
            w_play_mode (PlayMode): Play mode for the white player.
            b_play_mode (PlayMode): Play mode for the black player.
            save_game_log (bool, optional): Flag to enable game log saving. Defaults to False.

        Returns:
            None
        """
        self.w_play_mode , self.b_play_mode = w_play_mode, b_play_mode
        play_mode_functions = {
            PlayMode.user : self.user_play,
            PlayMode.random : self.random_play,
            PlayMode.next_best_nn: self.neural_net,
            PlayMode.agent: self.play_agent
        }
        self.w_play_function = play_mode_functions[w_play_mode]
        self.b_play_function = play_mode_functions[b_play_mode]
        if self.w_play_function == self.neural_net or self.b_play_function == self.neural_net:
            self.nn_engine = NeuralNetTFLite(model_path=os.path.join("AI","NueralNet2.tflite"))
        if self.w_play_function == self.play_agent:
            self.agent_w = Agent(player=Entity.white)
        if self.b_play_function == self.play_agent:
            self.agent_b = Agent(player=Entity.black)

        self.records = []
        self.state = State(TablutGame.initial_state, last_move=LastMoves.initial_state)
        self.board_size = len(self.state.board)
        self.game_finished = False
        self.selected_piece = None
        self.current_player = Entity.white
        self.winner = None
        self.if_save_game_log = save_game_log

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
        """
        Save the game log including move history and winner information to a text file.

        This method generates a string containing the move history and winner information
        from the game records and saves it to a text file. It includes details about each move,
        the board state after each move, and the final winner of the game.

        The file is named based on the winner, timestamp, move count, and player modes used during the game.

        Args:
            self: The Game instance to which this method belongs.

        Returns:
            None
        """
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
        """
        End the game and declare the winner or a draw.

        This method marks the end of the game, recording the winner or declaring a draw if no winner is specified.
        It updates the game state to indicate the game has finished and, if an AI agent is present,
        it saves statistical information regarding the agent's tree usage and running time.

        Args:
            self: The Game instance to which this method belongs.
            winner (Entity, optional): The Entity representing the winner (Entity.white or Entity.black).
                                    Defaults to None for a draw.

        Returns:
            None
        """
        ## These two global variables are just to calculate average tree running time, ignore
        global tree_use_counterS
        global total_time_treeS
        
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

        if self.if_save_game_log:
            self.save_game_log() 


    @staticmethod
    def who_is_opponent_of(player):
        """
        Determine the opponent of a given player in the game.

        This static method determines the opponent of the given player in the game.
        It takes the current player and returns the entity representing the opposing player.

        Args:
            player (Entity): The Entity representing the current player (Entity.white or Entity.black).

        Returns:
            Entity: The Entity representing the opponent player.
        """
        if player == Entity.white or player == Entity.king:
            return Entity.black 
        if player == Entity.black: 
            return Entity.white 


    @staticmethod
    def make_new_state(state:State, current_player, move_indexes:tuple):
        """
        Create a new game state based on a provided move for the current player.

        This static method generates a new game state by simulating a move on the board.
        It takes the current state, the current player, and the move indexes to determine
        the piece movement and creates a new state reflecting the consequences of that move.

        Args:
            state (State): The current game state.
            current_player: The Entity representing the current player (Entity.white or Entity.black).
            move_indexes (tuple): A tuple containing the indexes of the move (i, j, new_i, new_j).

        Returns:
            State: A new game state reflecting the result of the move.
        """
        i, j, new_i, new_j = move_indexes
        new_state = deepcopy(state.board)
        new_state[new_i][new_j] = new_state[i][j]
        new_state[i][j] = State().board[i][j] 
        state = State(new_state, last_move=current_player)
        return state 
        

    def change_player_turn(self):
        """ toggle whos turn it is """
        self.current_player = TablutGame.who_is_opponent_of(self.current_player)
    

    def update_board(self, move_indexes:tuple):
        """
        Update the game board with the specified move.

        Args:
            move_indexes: A tuple representing the move indexes (i, j, new_i, new_j).
            moved_by: The player who made the move.
        """
        i, j, new_i, new_j = move_indexes
        self.records.append(self.state)
        self.state = TablutGame.make_new_state(self.state, self.current_player, move_indexes=move_indexes)
        self.check_if_move_captures(new_i, new_j)
        self.check_game_has_winner(new_i, new_j)
        self.change_player_turn()


    def if_next_player_can_move(self):
        """ If next player cannot do any moves, return False """
        who_plays_next = TablutGame.who_is_opponent_of(self.current_player)
        possible_moves_for_next_player = self.state.possible_moves(who_plays_next)
        if not possible_moves_for_next_player:
            return False 
        return True


    def check_game_has_winner(self, i, j):
        """Checks if the last move has made anyone winner of the game

        Args:
            i (_type_): x position of the last move
            j (_type_): y position of the last move
        """        
        if self.state.if_black_captured_king(i, j): self.game_over(Entity.black)
        if self.state.if_king_escaped(i, j): self.game_over(Entity.white)
        if not self.if_next_player_can_move(): self.game_over(self.current_player)

    def white_move(self):
        self.w_play_function()

    def black_move(self):
        self.b_play_function()

    def neural_net(self):
        """
        Uses a neural network-based decision-making process to determine the next move for the current player.

        This function evaluates the possible moves available to the current player based on the current game state.
        For each possible move, it creates a new board state by simulating the move and evaluates the resulting state
        using a neural network-based scoring system. The move with the highest (for white) or lowest (for black) score
        is chosen as the best move and applied to update the game board.

        It iterates through all possible moves, evaluates them using the neural network, and selects the move with
        the most favorable (for white) or least favorable (for black) outcome.
        """
    
        possible_moves = self.state.possible_moves(self.current_player)
        possible_states = []
        for move_indexes in possible_moves:
            i, j, new_i, new_j = move_indexes
            new_board = deepcopy(self.state.board)
            new_board[new_i][new_j] = new_board[i][j]
            new_board[i][j] = State().board[i][j] 
            
            new_state = State(new_board, last_move=self.current_player)
            new_state.score =self.nn_engine.get_state_score(new_state)   
            possible_states.append(new_state)
        
        if self.current_player == Entity.white:
            index_of_state = max(enumerate(possible_states), key=lambda x: x[1].score)[0]
        elif self.current_player == Entity.black:
            index_of_state = min(enumerate(possible_states), key=lambda x: x[1].score)[0]
        self.update_board(possible_moves[index_of_state])


    def play_agent(self):
        # agent plays the next move
        if self.current_player==Entity.white:
            best_agent_move = self.agent_w.play_best_move(self.state)
        elif self.current_player==Entity.black:
            best_agent_move = self.agent_b.play_best_move(self.state)
        self.update_board(best_agent_move)


    def random_play(self):
        # play a random move
        self.update_board(self.__random_move(self.current_player))


    def user_play(self):
        """
        Wait for the user to make a move on the game board.

        This function listens for mouse input events and handles the selection and movement of pieces
        on the game board based on the user's actions.

        It allows the user to select pieces and move them according to the game rules:
        - If a square is clicked and no piece is selected, select the piece if it belongs to the current player.
        - If a piece is already selected, allow the user to move it to a valid destination square.

        Additionally, it visually indicates the selected piece and available moves on the game board
        by drawing semi-transparent colored squares.
        """
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
                    pm_l = []
                    for pm in self.selected_piece_possible_moves: pm_l.append(pm[-2:])
                    if (i,j) not in pm_l or (i,j) == self.selected_piece:
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
            for (_,_, i_, j_) in self.selected_piece_possible_moves:
                draw_rect_alpha(self.screen, (0, 255, 0, 127), (j_ * CELL_SIZE, i_ * CELL_SIZE, CELL_SIZE, CELL_SIZE))

    def play(self):
        """ run visualization and play next move """
        sleep(0.001)
        self.run_visualization()
        if self.current_player == Entity.white:
            self.white_move() 
        elif self.current_player == Entity.black:
            self.black_move()
        pygame.display.flip()


class PlayMode:   
    user = 0, #user plays
    random = 1, #moves will be random
    next_best_nn = 2, #only uses neural net
    agent = 3, #uses neural net and tree


if __name__=="__main__":
    while True:
        game = TablutGame(w_play_mode=PlayMode.agent, b_play_mode=PlayMode.random, save_game_log=False)
        while not game.game_finished:
            game.play()            
        pygame.quit()