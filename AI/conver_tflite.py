import tensorflow as tf

converter = tf.lite.TFLiteConverter.from_saved_model(r"AI\SavedModels\model5") 

tflite_converted_model = converter.convert()

with open('nueral_net_2.tflite', 'wb') as f:
  f.write(tflite_converted_model)