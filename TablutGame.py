from Utils import Entity, State, LastMoves
from copy import deepcopy
import random
from time import sleep
import pygame 
from Utils import CELL_SIZE
import datetime, os


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

    def __init__(self) -> None:
        """
        Initialize the Tablut game and Pygame for visualization.
        """
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

    def run_visualization(self):
        def draw_rect_alpha(surface, color, rect):
            shape_surf = pygame.Surface(pygame.Rect(rect).size, pygame.SRCALPHA)
            pygame.draw.rect(shape_surf, color, shape_surf.get_rect())
            surface.blit(shape_surf, rect)
        """
        Run the Pygame visualization of the game board.
        """
        self.screen.fill((255, 255, 255))
        self.state.pygame_visualize(self.screen)
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

        pygame.display.flip()


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

    def white_move(self):
        player_to_move = LastMoves.white
        self.update_board(self.__random_move(player_to_move), moved_by=player_to_move)

    def black_move(self):
        player_to_move=LastMoves.black
        self.update_board(self.__random_move(player_to_move), moved_by=player_to_move)

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
        filename = f"{self.winner}_{str(len(self.records))}_{timestamp}.txt"
        # Convert the string and save it to the file
        with open(os.path.join(save_dir, filename), "w") as file:
            file.write(string)


if __name__=="__main__":
    game = TablutGame()

    while not game.game_finished:
        game.run_visualization()
    
    pygame.quit()