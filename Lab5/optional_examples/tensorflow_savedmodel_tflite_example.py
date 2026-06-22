"""Optional example: TensorFlow/Keras model -> .keras/SavedModel/TFLite.

This file is for reading and exploration. It is not required for the main Lab 5
runtime because TensorFlow is much heavier than the core ONNX Runtime demo.
"""
from __future__ import annotations

# import tensorflow as tf
#
# model = tf.keras.Sequential([
#     tf.keras.layers.Input(shape=(4,)),
#     tf.keras.layers.Dense(8, activation="relu"),
#     tf.keras.layers.Dense(3),
# ])
# model.save("models/tiny_model.keras")
# model.export("models/tiny_savedmodel")
# converter = tf.lite.TFLiteConverter.from_keras_model(model)
# tflite_model = converter.convert()
# with open("models/tiny_model.tflite", "wb") as f:
#     f.write(tflite_model)
# print("Saved .keras, SavedModel, and .tflite examples")
