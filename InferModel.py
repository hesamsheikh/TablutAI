from tensorflow.keras.models import load_model 
import numpy as np 


model = load_model("model")
X = np.load("npys/X_test.npy")
Y = np.load("npys/Y_test.npy")
Y = np.expand_dims(Y, axis=1)
# X = X.reshape((X.shape[0], X.shape[2], X.shape[3], X.shape[1]))

y = model.predict(X)
mse = np.mean((Y - y) ** 2)
...