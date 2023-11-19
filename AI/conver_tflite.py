import tensorflow as tf

converter = tf.lite.TFLiteConverter.from_saved_model(r"AI\SavedModels\model_3") 

tflite_converted_model = converter.convert()

with open('nueral_net.tflite', 'wb') as f:
  f.write(tflite_converted_model)