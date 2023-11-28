from AI.ReadyDataset import state_to_nparray, initialize_nps
import numpy as np
# import tensorflow as tf
import tflite_runtime.interpreter as tflite



class NeuralNetTFLite:
    def __init__(self, model_path=r"model.tflite") -> None:
        self.interpreter = tflite.Interpreter(model_path=model_path)
        self.interpreter.allocate_tensors()

        # Get input and output details
        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()

        self.np_camps, self.np_castle, self.np_escapes = initialize_nps()

        # Warm up
        test_matrix = np.ones(self.input_details[0]['shape'], dtype=np.float32)
        self.interpreter.set_tensor(self.input_details[0]['index'], test_matrix)
        self.interpreter.invoke()

    def get_state_score(self, state):
        np_mat = state_to_nparray(self.np_camps, self.np_castle, self.np_escapes, state=state)
        np_mat = np.expand_dims(np_mat, axis=0)
        np_mat = np.transpose(np_mat, (0, 2, 3, 1))

        self.interpreter.set_tensor(self.input_details[0]['index'], np_mat.astype(np.float32))
        self.interpreter.invoke()

        output_data = self.interpreter.get_tensor(self.output_details[0]['index'])
        return output_data[0][0]
