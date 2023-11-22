from PIL import Image, ImageDraw
import math 
import pygame

CELL_SIZE = 60 

### Score functions to give a score to a game board, to use in training of Neural Net
def score_function_linear(x, x1):
    return (1/x1) * x

def score_function(x, x0, x1, steepness=0.5):
    if x <= x0:
        return 0
    elif x >= x1:
        return 1
    else:
        return 1 / (1 + math.exp(-steepness * (x - (x0 + x1) / 2)))
#####################################################################################

class Entity:
    square = "O"
    escape = "*"
    castle = "+"
    camp = "0"
    white = "W" 
    black = "B"
    king = "K"

class ServerCellType:
    white = "WHITE"
    black = "BLACK"
    king = "KING"
    empty = "EMPTY"

class LastMoves:
    white = "W"
    black = "B"
    initial_state = "I"

def resize_image(original_image):
    # Scale the image to fit within the cell size while maintaining aspect ratio
    return pygame.transform.scale(original_image, (CELL_SIZE, CELL_SIZE))

SquareImage = {
    # "W": image of white piece
    Entity.white: resize_image(pygame.image.load(r"Assets\w.png")),
    Entity.black: resize_image(pygame.image.load(r"Assets\b.png")),
    Entity.king: resize_image(pygame.image.load(r"Assets\k.png")),
    Entity.square: resize_image(pygame.image.load(r"Assets\e.png")),
    Entity.escape: resize_image(pygame.image.load(r"Assets\escape.png")),
    Entity.castle: resize_image(pygame.image.load(r"Assets\castle.png")),
    Entity.camp: resize_image(pygame.image.load(r"Assets\camp.png"))
}

class State:

    def __init__(self, state=None, last_move=None) -> None:
        """
        Initialize a state of the Tablut game.

        Args:
            state (list, optional): 2D list representing the game state. Defaults to None.
            last_move (LastMoves, optional): Last move made in the game. Defaults to None.
        """
        self.last_move = last_move
        if not state:
            self.board = [
            ['O', '*', '*', '0', '0', '0', '*', '*', 'O'],
            ['*', 'O', 'O', 'O', '0', 'O', 'O', 'O', '*'],
            ['*', 'O', 'O', 'O', 'O', 'O', 'O', 'O', '*'],
            ['0', 'O', 'O', 'O', 'O', 'O', 'O', 'O', '0'],
            ['0', '0', 'O', 'O', '+', 'O', 'O', '0', '0'],
            ['0', 'O', 'O', 'O', 'O', 'O', 'O', 'O', '0'],
            ['*', 'O', 'O', 'O', 'O', 'O', 'O', 'O', '*'],
            ['*', 'O', 'O', 'O', '0', 'O', 'O', 'O', '*'],
            ['O', '*', '*', '0', '0', '0', '*', '*', 'O']
            ]
        else: 
            self.board = state
        self.score = None


    def __str__(self) -> str:
        border = "+---" * len(self.board[0]) + "+"
        string = f"Moved By: {self.last_move} \n"
        string += border + "\n"
        for row in self.board:
            string += "| " + " | ".join(row) + " |" + "\n"
            string += border  + "\n"
        return string


    def if_black_captured_king(self, i, j):
        """check if a move by black has the king captured
        Args:
            i (_type_): new_move_i_index
            j (_type_): new_move_j_index
        Returns:
            _type_: has king been captured?
        """        
        if self.last_move == LastMoves.black:
            if self.if_king_captured(i, j): return True
        return False
    

    def where_is_king(self):
        """reutnr position of king"""
        for i in range(len(self.board)):
            for j in range(len(self.board[0])):
                if self.board[i][j] == Entity.king:
                    return (i,j)


    def if_king_escaped(self, i, j):
        """
        Check if the king has escaped due to a move by white.

        Args:
            i (int): New move row index.
            j (int): New move column index.

        Returns:
            bool: True if the king has escaped, False otherwise.
        """
        if self.last_move == LastMoves.white:
            if self.board[i][j] == Entity.king and State().board[i][j] == Entity.escape:
                    return True
        return False
    
    def if_king_captured(self, c_i, c_j):
        """
        Check if the king has been captured.

        Args:
            c_i (int): Column index of the king.
            c_j (int): Row index of the king.

        Returns:
            bool: True if the king has been captured, False otherwise.
        """
        for i in range(len(self.board)):
            for j in range(len(self.board[0])):
                if self.board[i][j] == Entity.king:
                    king_location = (i,j)
                    break

        center = (len(self.board) - 1) // 2  # Calculate the center square
        if king_location == (center, center):
            # King is in the center square, check if it's surrounded by black pieces
            center_neighbors = [(center - 1, center), (center + 1, center), (center, center - 1), (center, center + 1)]
            for i, j in center_neighbors:
                if self.board[i][j] != Entity.black:
                    return False  # King is not surrounded on all four sides
            return True  # King is surrounded by black pieces
        
        center_neighbors = [(center - 1, center), (center + 1, center), (center, center - 1), (center, center + 1)]
        if king_location in center_neighbors:
            ## king is near the castle, it must be surrounded by three black pieces and the castle
            k_i, k_j = king_location
            king_neighbors = [(k_i,k_j+1), (k_i,k_j-1), (k_i+1,k_j), (k_i-1,k_j)]
            for i, j in king_neighbors:
                if self.board[i][j] not in (Entity.black, Entity.castle):
                    return False 
            return True
        
        possible_directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        for rl, ud in possible_directions:
            new_i = c_i + ud  
            new_j = c_j + rl
            try:
                if self.board[new_i][new_j] == Entity.king:
                    new_i = c_i + 2*ud  
                    new_j = c_j + 2*rl
                    if self.board[new_i][new_j] == Entity.black:
                        return True
                    break
            except IndexError: return False


    def check_if_index_is_inside_board(self, i, j):
        ## Check whether index is inside the board
        board_size = len(self.board)
        return 0 <= i < board_size and 0 <= j < board_size
    
    def possible_moves(self, for_player=Entity.white):
        """
        Get a list of possible moves for the specified player.
        Args:
            for_player: The player for whom to find possible moves (Entity.white or Entity.black).
        Returns:
            A list of possible move tuples, each containing (i, j, new_i, new_j).
        """
        possible_states = []
        if for_player == Entity.white:
            piece_should_be = [Entity.white, Entity.king]
        elif for_player == Entity.black:
            piece_should_be = [Entity.black]        

        for i in range(len(self.board)):
            for j in range(len(self.board[0])):
                if self.board[i][j] in piece_should_be:
                    possible_states.extend(self.possible_moves_for_index(i, j))
        return possible_states
    

    def possible_moves_for_index(self, i, j):
        """
        Get a list of possible moves for the piece at the specified index.
        Args:
            i: Row index of the piece.
            j: Column index of the piece.
        Returns:
            A list of possible move tuples, each containing (i, j, new_i, new_j).
        """
        possible_states = []
        destination_should_be = [Entity.square, Entity.escape]
        black_pieces_middle_of_camp = [(0,4),(4,0),(4,8),(8,4)]

        if (i,j) in black_pieces_middle_of_camp and self.board[i][j] == Entity.black:
            destination_should_be = destination_should_be + [Entity.camp]

        possible_directions = [(0, 1), (0, -1), (1, 0), (-1, 0)] 
        for rl, ud in possible_directions:
            counter = 0
            while True:
                counter += 1
                new_i = i + counter*rl  
                new_j = j + counter*ud
                if self.check_if_index_is_inside_board(new_i, new_j) and \
                    self.board[new_i][new_j] in destination_should_be:
                    possible_states.append((i, j, new_i, new_j))
                else: break
        return possible_states
    
    def pygame_visualize(self, screen):
        """
        Visualize the game state using Pygame.

        Args:
            screen: Pygame screen object.
        """
        for row in range(len(self.board)):
            for col in range(len(self.board[0])):
                piece = self.board[row][col]
                piece_image = SquareImage[piece]
                piece_rect = piece_image.get_rect()
                piece_rect.topleft = (col * CELL_SIZE, row * CELL_SIZE)
                screen.blit(piece_image, piece_rect)
                pygame.draw.rect(screen, (0,0,0),
                                (col * CELL_SIZE, row * CELL_SIZE, CELL_SIZE, CELL_SIZE), 2)

    def visualize_board(self):
        """
        Visualize the game board using Pillow (PIL) library.
        Displays the board using the default image viewer.
        """
        white_img_path = Image.open(r"D:\tablut_bot\Assets\w.png")
        black_img_path = Image.open(r"D:\tablut_bot\Assets\b.png")
        king_img_path = Image.open(r"D:\tablut_bot\Assets\k.png")
        empty_cell_color = (255,233,127)
        
        square_size = 40  # Adjust the size of each square as needed
        board_width = len(self.board[0]) * square_size
        board_height = len(self.board) * square_size

        board_image = Image.new("RGB", (board_width, board_height), "white")
        draw = ImageDraw.Draw(board_image)

        for row_idx, row in enumerate(self.board):
            for col_idx, cell in enumerate(row):
                left = col_idx * square_size
                top = row_idx * square_size
                right = left + square_size
                bottom = top + square_size
                

                # You can customize this part to load and paste the appropriate image based on the 'cell' value
                if cell == Entity.white:
                    cell_image = white_img_path
                elif cell == Entity.black:
                    cell_image = black_img_path
                elif cell == Entity.king:
                    cell_image = king_img_path
                else:
                    cell_image = Image.new("RGB", (square_size, square_size), empty_cell_color)

                cell_image = cell_image.resize((square_size, square_size), Image.ANTIALIAS)
                board_image.paste(cell_image, (left, top, right, bottom))
                # Draw a border (grid line) between cells
                draw.rectangle((left, top, right, bottom), outline="black")

        board_image.show()  # Show the board using the default image viewer
