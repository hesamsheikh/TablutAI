from AI.ReadyDataset import state_to_nparray, initialize_nps
import numpy as np
from tensorflow.keras.models import load_model
import tensorflow as tf 


class NeuralNetTensorFlow:
    def __init__(self, model_path=r"AI\SavedModels\model_3") -> None:
        self.model = load_model(model_path) 
        self.np_camps, self.np_castle, self.np_escapes = initialize_nps()
        
        # Warm up
        test_matrix = np.expand_dims(np.ones((self.model.input_shape[1:])), axis=0)
        self.model.predict(test_matrix)

    def get_state_score(self, state):
        np_mat = state_to_nparray(self.np_camps, self.np_castle, self.np_escapes, state=state)
        np_mat = np.expand_dims(np_mat, axis=0)
        np_mat = np.transpose(np_mat, (0, 2, 3, 1))
        return self.model.predict(np_mat)[0][0]

