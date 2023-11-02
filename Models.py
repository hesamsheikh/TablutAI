from tensorflow.keras.layers import Input, Conv2D, Flatten, Dense, MaxPooling2D
from tensorflow.keras import Model

def build_model_1():
    board3d = Input(shape=(9,9,6))
    x = board3d
    x = Conv2D(filters=16, kernel_size=(3,3), padding='same', activation='relu')(x)
    x = Conv2D(filters=64, kernel_size=(3,3), padding='same', activation='relu')(x)
    x = Conv2D(filters=96, kernel_size=(3,3), padding='same', activation='relu')(x)
    x = Flatten()(x)
    x = Dense(64)(x)
    x = Dense(1, 'tanh')(x)
    m = Model(inputs=board3d, outputs=x)
    return m


def build_model_2():
    board3d = Input(shape=(9,9,6))
    x = board3d
    x = Flatten()(x)
    x = Dense(512, activation='relu')(x)
    x = Dense(256, activation='relu')(x)
    x = Dense(16, activation='relu')(x)
    x = Dense(1, 'tanh')(x)
    m = Model(inputs=board3d, outputs=x)
    return m
