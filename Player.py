from Utils import Entity, State
import random
from pyvis.network import Network
import networkx as nx
import matplotlib.pyplot as plt
from copy import deepcopy
from time import time


def mean(lst):
    return sum(lst) / len(lst)

class Node:     
    def __init__(self, state:State, player=Entity.white, depth=0, last_move_index=None):
        self.state = state
        self.who_has_to_play = player
        self.depth = depth 
        self.score = 0
        self.children = []
        self.node_id = ''
        self.last_move_index = last_move_index

    def update_node_id(self):
        self.node_id = self.get_node_id()

    def generate_children(self):
        from TablutGame import TablutGame
        if self.depth == MaximumDepth-1 and self.who_has_to_play == Entity.white:
            king_pos = self.state.where_is_king()
            possible_moves = self.state.possible_moves_for_index(*king_pos)
        else:
            possible_moves = self.state.possible_moves(for_player=self.who_has_to_play)
        
        # Prioritze the moves that have more probablity to win
        if self.who_has_to_play == Entity.white:
            new_possible_moves_list = []
            for ndx,(i,j,new_i,new_j) in enumerate(possible_moves):
                if (i,j) == self.state.where_is_king():
                    new_possible_moves_list.append((i,j,new_i,new_j))
                    del possible_moves[ndx]
            new_possible_moves_list.extend(possible_moves)
            possible_moves = new_possible_moves_list
        
        if self.who_has_to_play == Entity.black:
            new_possible_moves_list = []
            for ndx, (i,j,new_i,new_j) in enumerate(possible_moves):
                index_neighbors_of_dest = [(new_i,new_j+1), (new_i,new_j-1), (new_i+1,new_j), (new_i-1,new_j)]
                for x,y in index_neighbors_of_dest:
                    try:
                        if Entity.king == self.state.board[x][y]:
                            new_possible_moves_list.append(possible_moves[ndx])
                            del possible_moves[ndx]
                    except IndexError:
                        pass
            new_possible_moves_list.extend(possible_moves)
            possible_moves = new_possible_moves_list
        
        # The last move of black must be close to the king
        if self.depth == MaximumDepth-1 and self.who_has_to_play == Entity.black:
            last_moves_black = []
            for i, (_,_,dest_i,dest_j) in enumerate(possible_moves):
                index_neighbors_of_dest = [(dest_i,dest_j+1), (dest_i,dest_j-1), (dest_i+1,dest_j), (dest_i-1,dest_j)]
                for x,y in index_neighbors_of_dest:
                    try:
                        if Entity.king == self.state.board[x][y]:
                            last_moves_black.append(possible_moves[i])
                    except IndexError:
                        pass
            possible_moves = last_moves_black

        for move_tuple in possible_moves:
            i, j, new_i, new_j = move_tuple
            #create new child 
            child_state = TablutGame.make_new_state(self.state, self.who_has_to_play, move_tuple)
            child_node = Node(state=child_state,
                            player=TablutGame.who_is_opponent_of(self.who_has_to_play), 
                            depth=self.depth+1,
                            last_move_index=(i, j, new_i, new_j))
            self.children.append(child_node)

    def get_node_id(self):
        random_number = random.randint(0, 10000)
        return f"{random_number}--{self.score}-{self.depth}-{self.who_has_to_play}"  # Define a unique identifier for each node


class Tree:
    def __init__(self, root_node:Node, maximum_depth=3, for_player=Entity.white) -> None:
        self.root = root_node
        self.maximum_depth = maximum_depth
        self.nodes_visited = 0
        self.for_player = for_player
        self.dont_visit_siblings = False

    def search_tree(self, node=Node):
        self.nodes_visited += 1
        black_wins = False
        white_wins = False

        if node.last_move_index:
            i, j, new_i, new_j = node.last_move_index
            black_wins = node.state.if_black_captured_king(new_i, new_j)
            white_wins = node.state.if_king_escaped(new_i, new_j)
            if self.for_player == Entity.white:
                if white_wins: 
                    node.score = 1
                elif black_wins: 
                    node.score = -100
            elif self.for_player == Entity.black:
                if white_wins: 
                    node.score = -100
                elif black_wins: 
                    node.score = 1

        if node.depth == 1 and not node.children:
            node.score *= 5

        if black_wins:
            if self.for_player == Entity.white:
                return False 
            elif self.for_player == Entity.black:
                return True
        elif white_wins:
            if self.for_player == Entity.black:
                return False 
            elif self.for_player == Entity.white:
                return True 

        if node.depth < self.maximum_depth:
            node.generate_children()

            for child in node.children:
                node_is_successful = self.search_tree(child)
                if node_is_successful and node.depth % 2 == 0: 
                    break

            children_score = [n.score for n in node.children]
            if children_score:
                if (node.who_has_to_play == Entity.black and self.for_player == Entity.white)\
                or (node.who_has_to_play == Entity.white and self.for_player == Entity.black):
                    node.score = mean(children_score)
                elif (node.who_has_to_play == Entity.black and self.for_player == Entity.black)\
                or (node.who_has_to_play == Entity.white and self.for_player == Entity.white):
                    node.score = max(children_score)

        node.update_node_id()


    def get_best_node(self):
        best_node = max(self.root.children, key=lambda x: x.score)
        return best_node.last_move_index

    def create_networkx_graph(self):
        graph = nx.DiGraph()
        added_nodes = set()

        def add_node_to_graph(node):
            node_id = node.node_id
            if node_id not in added_nodes:
                graph.add_node(node_id)
                added_nodes.add(node_id)
            for child in node.children:
                child_id = child.node_id
                if child_id not in added_nodes:
                    graph.add_node(child_id)
                    added_nodes.add(child_id)
                graph.add_edge(node_id, child_id)
                # add_node_to_graph(child)

        add_node_to_graph(self.root)
        return graph


class Agent:
    def __init__(self, player) -> None:
        from NueralNetTFLite import NeuralNetTFLite
        self.nn_engine = NeuralNetTFLite(model_path=r"AI\nueral_net.tflite")
        self.player = player
        self.steps_played = 0
        self.use_tree_threshhold = {Entity.black:0.0, Entity.white:0.0}
        self.start_tree_after_this_many_moves = {Entity.black: 3, Entity.white: 3}
        self.total_time_tree = 0 
        self.tree_use_counter = 0

    def infer_nueral_net(self, state:State):
        """use nueral net to get the best move
        Args:
            state (State): the current state we want to get best move from 
        Returns:
            _type_: best move
        """        
        possible_moves = state.possible_moves(self.player)
        possible_states = []
        for move_indexes in possible_moves:
            i, j, new_i, new_j = move_indexes
            new_board = deepcopy(state.board)
            new_board[new_i][new_j] = new_board[i][j]
            new_board[i][j] = State().board[i][j] 
            
            new_state = State(new_board, last_move=self.player)
            new_state.score =self.nn_engine.get_state_score(new_state)
            possible_states.append(new_state)
        
        if self.player == Entity.white:
            index_of_state = max(enumerate(possible_states), key=lambda x: x[1].score)[0]
        elif self.player == Entity.black:
            index_of_state = min(enumerate(possible_states), key=lambda x: x[1].score)[0]
        return possible_moves[index_of_state]


    def play_best_move(self, state:State):
        self.steps_played += 1
        center = (len(state.board) - 1) // 2
        king_in_the_center = state.where_is_king() == (center,center)
            
        if self.steps_played > self.start_tree_after_this_many_moves[self.player]:
            if self.player == Entity.black and king_in_the_center:
                return self.infer_nueral_net(state)
            
            st = time()
            tree = Tree(Node(state=state, player=self.player), maximum_depth=MaximumDepth, for_player=self.player)
            tree.search_tree(node=tree.root)
            et = time() - st 
            self.tree_use_counter += 1
            self.total_time_tree += et

            if tree.root.score > self.use_tree_threshhold[self.player]:
                return tree.get_best_node()
            else:
                return self.infer_nueral_net(state)
        else:
            return self.infer_nueral_net(state)

MaximumDepth = 3
...