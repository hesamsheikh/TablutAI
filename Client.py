import socket
import struct
import json
import sys
from TablutGame import TablutGame, PlayMode
from Utils import Entity, State, LastMoves, ServerCellType

class Client:
    CASTLE_LOCATION = (4, 4)
    LEFT_CAMP_LOCATION = [(i, 0) for i in range(3, 6)] + [(4, 1)]
    RIGHT_CAMP_LOCATION = [(i, 8) for i in range(3, 6)] + [(4, 7)]
    UP_CAMP_LOCATION = [(0, i) for i in range(3, 6)] + [(1, 4)]
    DOWN_CAMP_LOCATION = [(8, i) for i in range(3, 6)] + [(7, 4)]
    CAMP_LOCATIONS = LEFT_CAMP_LOCATION + RIGHT_CAMP_LOCATION + UP_CAMP_LOCATION + DOWN_CAMP_LOCATION
    ESCAPE_LOCATIONS = [cell for j in [[[(i, j), (j, i)] for j in [1,2,6,7]] for i in [0, 8]] for k in j for cell in k]

    def __init__(self, color, timeout, server_ip):
        self.player_name = 'Nova'
        self.color = color.lower()
        self.timeout = timeout
        self.server_ip = server_ip
        if self.color not in ['white', 'black']:
            raise Exception('If you play, you are either white or black.')
        self.port = 5800 if self.color == 'white' else 5801
        self.server_address = (self.server_ip, self.port)

    @staticmethod
    def recvall(sock, n):
        # Helper function to recv n bytes or return None if EOF is hit
        data = b''
        while len(data) < n:
            packet = sock.recv(n - len(data))
            if not packet:
                return None
            data += packet
        return data

    def initiate_connection(self, sock):
        sock.connect(self.server_address)
        sock.send(struct.pack('>i', len(self.player_name)))
        sock.send(self.player_name.encode())

    @classmethod
    def convert_cell(cls, current_cell, cell_location):
        if current_cell == ServerCellType.white:
            return Entity.white
        if current_cell == ServerCellType.black:
            return Entity.black
        if current_cell == ServerCellType.king:
            return Entity.king
        if cell_location == cls.CASTLE_LOCATION:
            return Entity.castle
        if cell_location in cls.CAMP_LOCATIONS:
            return Entity.camp
        if cell_location in cls.ESCAPE_LOCATIONS:
            return Entity.escape
        return Entity.square

    @classmethod
    def convert_board(cls, current_board):
        return [[cls.convert_cell(cell,(row_index, column_index)) for column_index, cell in enumerate(row)] for row_index, row in enumerate(current_board)]

    def make_move(self, game):
        # TODO use the best move instead of random move
        x_from, y_from, x_to, y_to = game.__random_move(for_player=Entity.white if self.color == 'white' else Entity.black)
        print(chr(x_from + ord('a')) + y_from, chr(x_to + ord('a')) + y_to)
        return chr(x_from + ord('a')) + y_from, chr(x_to + ord('a')) + y_to

    def read_from_server(self, sock):
        len_bytes = struct.unpack('>i', self.recvall(sock, 4))[0]
        current_state_server_bytes = sock.recv(len_bytes)
        return json.loads(current_state_server_bytes)

    def send_move(self, sock, game):
        from_cell, to_cell = self.make_move(game)
        move_for_server = json.dumps({
            "from": from_cell,
            "to": to_cell,
            "turn": self.color.upper()[:1]
        })
        sock.send(struct.pack('>i', len(move_for_server)))
        sock.send(move_for_server.encode())


    def play_game(self, sock):
        game = TablutGame(w_play_mode=PlayMode.next_best_nn,b_play_mode=PlayMode.next_best_nn)
        if self.color == 'white':
            json_current_state_server = self.read_from_server(sock)
            current_board = json_current_state_server['board']
            current_converted_board = self.convert_board(current_board)
            if current_converted_board != game.state.board:
                raise Exception('Wrong starting table.')
            self.send_move(sock, game)
        while True:
            json_current_state_server = self.read_from_server(sock)
            current_board = json_current_state_server['board']
            current_turn = json_current_state_server['turn'].lower()
            if current_turn != self.color:
                continue
            current_converted_board = self.convert_board(current_board)
            state = State(current_converted_board,
                          last_move=LastMoves.black if self.color == 'white' else LastMoves.white)
            game.state = state
            self.send_move(sock, game)


    def main(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            self.initiate_connection(sock)
            self.play_game(sock)



if __name__ == '__main__':
    color, timeout, server_ip =  sys.argv[1:]
    client = Client(color, timeout, server_ip)
    client.main()