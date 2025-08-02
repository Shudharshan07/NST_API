import tensorflow as tf
import tensorflow_hub as hub
from PIL import Image
import numpy as np
from io import BytesIO

class NST:
    def LoadImage(self, path):
        img = tf.image.decode_image(path, channels=3)
        img = tf.image.convert_image_dtype(img, tf.float32)


        shape = tf.cast(tf.shape(img)[:-1], tf.float32)
        scale = 512 / max(shape)
        shape = tf.cast(shape * scale, tf.int32)

        img = tf.image.resize(img, shape)
        img = img[tf.newaxis, :]

        return img
    
    def ToImage(self, arr):
        arr = arr * 255
        arr = np.array(arr, dtype="uint8")

        if np.ndim(arr)>3:
            assert arr.shape[0] == 1
            arr = arr[0]

        img = Image.fromarray(arr)
        bio = BytesIO()
        bio.name = "OUTPUT.png"
        img.save(bio, format="PNG")
        bio.seek(0)

        return bio

    def __call__(self, Content_path, Style_path):
        model = hub.load('https://tfhub.dev/google/magenta/arbitrary-image-stylization-v1-256/2')
        Content = self.LoadImage(Content_path)
        Style = self.LoadImage(Style_path)

        output = model(tf.constant(Content), tf.constant(Style))[0]

        return self.ToImage(output)


