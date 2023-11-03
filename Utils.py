from PIL import Image, ImageDraw
import math 
import pygame

CELL_SIZE = 60 

def score_function(x, x0, x1, steepness=0.5):
    if x <= x0:
        return 0
    elif x >= x1:
        return 1
    else:
        return 1 / (1 + math.exp(-steepness * (x - (x0 + x1) / 2)))

class Entity:
    square = "O"
    escape = "*"
    castle = "+"
    camp = "0"
    white = "W" 
    black = "B"
    king = "K"

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
            destination_should_be = [Entity.square, Entity.escape]
        elif for_player == Entity.black:
            piece_should_be = [Entity.black]
            destination_should_be = [Entity.square, Entity.escape]

        for i in range(len(self.board)):
            for j in range(len(self.board[0])):
                if self.board[i][j] in piece_should_be:
                    ## possible move  
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

        possible_directions = [(0, 1), (0, -1), (1, 0), (-1, 0)] 
        for rl, ud in possible_directions:
            counter = 0
            while True:
                counter += 1
                new_i = i + counter*rl  
                new_j = j + counter*ud
                if self.check_if_index_is_inside_board(new_i, new_j) and \
                    self.board[new_i][new_j] in destination_should_be:
                    possible_states.append((new_i, new_j))
                else: break
        return possible_states
    
    def pygame_visualize(self, screen):
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
