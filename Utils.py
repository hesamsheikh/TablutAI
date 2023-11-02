from PIL import Image, ImageDraw
import math 


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
