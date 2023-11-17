from TablutGame import TablutGame, NeuralNet, PlayMode
from Utils import Entity, State
import graphviz
import random
import os
graphviz.render.engine = 'dot'
graphviz.render.executable = r"c:\Program Files\Graphviz\bin\dot.exe"  # Replace with your actual Graphviz executable path
os.environ["PATH"] += os.pathsep + r"C:\Program Files\Graphviz\bin"


class Node:     
    def __init__(self, state, player=Entity.white, depth=0):
        self.state = state
        self.player = player
        self.depth = depth 
        self.score = 0
        self.children = []
        self.traversed = False 
        self.node_id = self.get_node_id()

    def generate_children(self):
        children = []
        for move in self.state.possible_moves(for_player=self.player):
            #create new child 
            child_state = game.make_new_state(move)
            child_node = Node(state=child_state,
                            player=game.who_is_opponent_of(self.player), 
                            depth=self.depth+1)
            children.append(child_node)
        self.children = children

    def get_node_id(self):
        random_number = random.randint(0, 10000)
        return f"{random_number}-{self.depth}-{self.player}"  # Define a unique identifier for each node


class Tree:
    def __init__(self, root_node:Node, maximum_depth=3) -> None:
        self.root = root_node
        self.maximum_depth = maximum_depth
        self.counter = 0
        # for depth in range(maximum_depth):

    def search_tree(self, node=None):
        if node is None:
            node = self.root

        self.counter += 1
        node.traversed = True
        if node.depth < self.maximum_depth:
            node.generate_children()
            for child in node.children:
                self.search_tree(child)
            
    def create_dot(self):
        dot = graphviz.Digraph(comment='Tree Visualization')
        added_nodes = set()

        def add_node_to_dot(node):
            node_id = node.node_id
            if node_id not in added_nodes:
                dot.node(node_id)
                added_nodes.add(node_id)
                for child in node.children:
                    child_id = child.node_id
                    if child_id not in added_nodes:
                        dot.node(child_id)
                        added_nodes.add(child_id)
                    dot.edge(node_id, child_id)
                    add_node_to_dot(child)

        add_node_to_dot(self.root)
        return dot


initial_state = State(TablutGame.initial_state)
game = TablutGame(w_play_mode=PlayMode.random, b_play_mode=PlayMode.random)
tree = Tree(Node(state=initial_state), maximum_depth=3)
tree.search_tree(node=tree.root)

dot = tree.create_dot()
dot.format = 'png'  # Set the output format to PNG (or any other supported format)
dot.render('tree', view=True)  # Renders the graph to a file named 'tree.png' and displays it
...