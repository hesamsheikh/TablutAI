from Utils import Entity, State
import random
from copy import deepcopy
from time import time
import os 
import json


def mean(lst):
    return sum(lst) / len(lst)

class Node:     
    def __init__(self, state:State, player=Entity.white, depth=0, last_move_index=None):
        """
        Initializes a node in the game tree.

        Args:
            state (State): The game state associated with the node.
            player (Entity, optional): The player to make the move at this node. Defaults to Entity.white.
            depth (int, optional): The depth of the node in the game tree. Defaults to 0.
            last_move_index (tuple, optional): Index of the last move made. Defaults to None.
        """
        self.state = state
        self.who_has_to_play = player
        self.depth = depth 
        self.score = 0
        self.children = []
        self.node_id = ''
        self.last_move_index = last_move_index

    def update_node_id(self):
        """
        Update the unique identifier of the node based on its attributes.
        """
        self.node_id = self.get_node_id()

    def generate_children(self):
        """
        Generates child nodes for the current node based on possible moves in the game.

        It prioritizes moves and constraints based on the current state and player's turn.
        """
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
            for pm in possible_moves:
                if pm not in new_possible_moves_list:
                    new_possible_moves_list.append(pm)
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
        """
        Generates a unique identifier for the node based on its attributes.

        Returns:
            str: Unique identifier for the node.
        """
        random_number = random.randint(0, 10000)
        return f"{random_number}--{self.score}-{self.depth}-{self.who_has_to_play}"  # Define a unique identifier for each node


class Tree:
    def __init__(self, root_node:Node, maximum_depth=3, for_player=Entity.white) -> None:
        """
        Initializes a tree with a root node and parameters for tree search.

        Args:
            root_node (Node): The root node of the tree.
            maximum_depth (int, optional): The maximum depth to search in the tree. Defaults to 3.
            for_player (Entity, optional): The player for whom the search is performed. Defaults to Entity.white.
        """
        self.root = root_node
        self.maximum_depth = maximum_depth
        self.nodes_visited = 0
        self.for_player = for_player
        self.dont_visit_siblings = False
        
        self.win_reward = 1
        self.lose_penalty = -100


    def search_tree(self, node=Node):
        """
        Recursively explores the tree to search for the best move using minimax algorithm.

        Args:
            node (Node): The node being explored. Defaults to root node.

        Returns:
            bool: True if the current player wins; False otherwise.
        """
        self.nodes_visited += 1
        black_wins = False
        white_wins = False

        if node.last_move_index:
            _, _, new_i, new_j = node.last_move_index
            black_wins = node.state.if_black_captured_king(new_i, new_j)
            white_wins = node.state.if_king_escaped(new_i, new_j)
            if self.for_player == Entity.white:
                if white_wins: 
                    node.score = self.win_reward
                elif black_wins: 
                    node.score = self.lose_penalty
            elif self.for_player == Entity.black:
                if white_wins: 
                    node.score = self.lose_penalty
                elif black_wins: 
                    node.score = self.win_reward

        # If the next best move wins the game, increase its score
        #  so the tree selects the move that is closest to winning the game
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
                if node_is_successful==True and node.depth % 2 == 0: 
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
        """
        Gets the best node based on calculated scores in the tree.

        Returns:
            tuple: Index of the best move found in the tree.
        """
        best_node = max(self.root.children, key=lambda x: x.score)
        return best_node.last_move_index


    def create_and_save_pyvis_network(self, file_name="tree_visualization.html"):
        """
        Creates and saves a Pyvis network representation of the entire tree to an HTML file.

        Args:
            file_name (str): Name of the HTML file to save the visualization. Default is "tree_visualization.html".
        """
        from pyvis.network import Network

        net = Network(directed=True, layout=True)
        added_nodes = set()

        def add_node_to_network(node):
            node_id = node.node_id
            if node_id not in added_nodes:
                net.add_node(node_id)
                added_nodes.add(node_id)
            for child in node.children:
                child_id = child.node_id
                if child_id not in added_nodes:
                    net.add_node(child_id)
                    added_nodes.add(child_id)
                net.add_edge(node_id, child_id)
                add_node_to_network(child)  # Recursively traverse the entire tree

        add_node_to_network(self.root)
        options = {
            "layout": {
                "hierarchical": {
                    "enabled": True,
                    "direction": "UD",
                    "sortMethod": "directed",
                    "parentCentralization": True
                }
            },
            "edges": {
                "arrows": {"to": {"enabled": True}}
            },
            "physics": {
                "enabled": False
            },
            "interaction": {
                "hover": True,
                "zoomView": True
            },
            "nodes": {
                "size": 50,
                "color": "skyblue",
                "shape": "dot"
            }
        }
        net.set_options(json.dumps(options))
        # net.show_buttons(filter_=['layout'])  # Show the layout button in the generated HTML
        net.write_html(file_name)


class Agent:
    def __init__(self, player) -> None:
        """
        Initializes an Agent using a neural network model for decision making.

        Args:
            player (Entity): The player type (Entity.black or Entity.white).
        """
        from NueralNetTFLite import NeuralNetTFLite
        self.nn_engine = NeuralNetTFLite(model_path=os.path.join("AI","NueralNet2.tflite"))
        self.player = player
        self.steps_played = 0
        self.use_tree_threshhold = {Entity.black:0.0, Entity.white:0.0}
        self.start_tree_after_this_many_moves = {Entity.black: 4, Entity.white: 4}
        self.total_time_tree = 0 
        self.tree_use_counter = 0


    def infer_nueral_net(self, state:State):
        """
        Uses the neural network to infer the best move based on the current state.

        Args:
            state (State): The current state for which the best move is to be inferred.

        Returns:
            tuple: The best move based on the neural network's prediction.
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
        """
        Plays the best move based on the given state, using a combination of neural network and tree search.

        Args:
            state (State): The current state of the game.

        Returns:
            tuple: The best move to play based on the decision-making process (neural network or tree search).
        """
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