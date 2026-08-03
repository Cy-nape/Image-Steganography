# lsb.py
from PIL import Image
import numpy as np
import logging
import os

logger = logging.getLogger(__name__)

def set_lsb(value, bit):
    """Set the least significant bit of a pixel value"""
    try:
        value = np.uint8(value)
        return np.uint8(value | 1) if bit == 1 else np.uint8(value & 0xFE)
    except Exception as e:
        logger.error(f"Error setting LSB: {str(e)}")
        raise

def lsb_encode(image_path, binary_message, message_length, pipeline_flag, output_path='encoded_image.png'):
    """Encode binary message into image using LSB steganography"""
    try:
        if not os.path.exists(image_path):
            raise FileNotFoundError("Input image not found")

        if not binary_message:
            raise ValueError("Empty binary message provided")

        # Open and convert image to RGB to strip alpha and standardize channels
        image = Image.open(image_path).convert('RGB')
        img_array = np.array(image)
        
        # Check if image has enough capacity (flag: 8 bits, length: 32 bits)
        if len(binary_message) + 40 > img_array.size:
            raise ValueError("Message too large for this image")

        # Flatten image
        flat_image = img_array.flatten()
        
        # 8 bits for flag, 32 bits for length
        flag_bits = format(pipeline_flag, '08b')
        length_bits = format(message_length, '032b')
        
        # Encode flag
        for i, bit in enumerate(flag_bits):
            flat_image[i] = set_lsb(flat_image[i], int(bit))
            
        # Encode length
        for i, bit in enumerate(length_bits):
            flat_image[i + 8] = set_lsb(flat_image[i + 8], int(bit))
        
        # Encode message
        for i, bit in enumerate(binary_message):
            flat_image[i + 40] = set_lsb(flat_image[i + 40], int(bit))

        # Reshape and save
        img_array = flat_image.reshape(img_array.shape)
        encoded_image = Image.fromarray(img_array)
        encoded_image.save(output_path, 'PNG')

        logger.info(f"Message encoded successfully in image: {output_path}")
        return output_path

    except Exception as e:
        logger.error(f"Error in LSB encoding: {str(e)}")
        raise

def lsb_decode(image_path):
    """Decode message from LSB-encoded image"""
    try:
        if not os.path.exists(image_path):
            raise FileNotFoundError("Encoded image not found")

        # Open and process image (must convert to RGB to match encoding)
        image = Image.open(image_path).convert('RGB')
        img_array = np.array(image)
        flat_image = img_array.flatten()

        # Extract flag first (first 8 bits)
        flag_bits = ''.join(str(flat_image[i] & 1) for i in range(8))
        pipeline_flag = int(flag_bits, 2)

        # Extract length (next 32 bits)
        length_bits = ''.join(str(flat_image[i] & 1) for i in range(8, 40))
        message_length = int(length_bits, 2)

        # Extract message using the length we found
        binary_message = ''.join(str(flat_image[i] & 1) for i in range(40, 40 + message_length))

        logger.info("Message extracted successfully from image")
        return pipeline_flag, binary_message

    except Exception as e:
        logger.error(f"Error in LSB decoding: {str(e)}")
        raise