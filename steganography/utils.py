# utils.py
from .huffman import HuffmanCoding
from .lsb import lsb_encode, lsb_decode
from . import crypto
import logging

logger = logging.getLogger(__name__)

def encode_message(image_path, message, output_path='encoded_image.png', pipeline='secure', passphrase=None):
    """
    Complete encoding process based on pipeline selection.
    Args:
        image_path: Path to input image
        message: Message to encode
        output_path: Path to save the encoded image
        pipeline: 'basic' or 'secure'
        passphrase: Required if pipeline is 'secure'
    Returns:
        Tuple of (encoded image path, huffman instance, message_length)
    """
    try:
        huffman = HuffmanCoding()
        binary_message = huffman.encode(message)
        logger.info("Huffman encoding completed")

        if pipeline == 'secure':
            if not passphrase:
                raise ValueError("Passphrase required for secure pipeline")
            
            # Prepend 32-bit length header to handle padding
            bit_length = len(binary_message)
            bit_length_str = format(bit_length, '032b')
            binary_message_with_length = bit_length_str + binary_message
            
            # Pad to multiple of 8 bits
            padded_binary_message = binary_message_with_length
            if len(padded_binary_message) % 8 != 0:
                padded_binary_message = padded_binary_message.ljust(len(padded_binary_message) + (8 - len(padded_binary_message) % 8), '0')
            
            plaintext_bytes = bytes(int(padded_binary_message[i:i+8], 2) for i in range(0, len(padded_binary_message), 8))
            
            # Encrypt
            ciphertext_bytes = crypto.encrypt(plaintext_bytes, passphrase)
            
            # Convert ciphertext back to binary string for LSB
            final_binary_message = ''.join(format(byte, '08b') for byte in ciphertext_bytes)
            pipeline_flag = 1
            logger.info("Secure pipeline encryption completed")
        else:
            final_binary_message = binary_message
            pipeline_flag = 0

        message_length = len(final_binary_message)
        encoded_image_path = lsb_encode(image_path, final_binary_message, message_length, pipeline_flag, output_path)
        logger.info("LSB encoding completed")

        return encoded_image_path, huffman

    except Exception as e:
        logger.error(f"Error in message encoding: {str(e)}")
        raise

def decode_message(image_path, huffman, passphrase=None):
    """
    Complete decoding process based on embedded pipeline flag.
    Args:
        image_path: Path to encoded image
        huffman: HuffmanCoding instance used for encoding
        passphrase: Required if pipeline flag indicates secure
    Returns:
        Decoded message
    """
    try:
        pipeline_flag, binary_message = lsb_decode(image_path)
        logger.info("LSB decoding completed")

        if pipeline_flag == 1:
            if not passphrase:
                raise ValueError("Passphrase required for secure pipeline")
            
            # Convert binary string to bytes
            ciphertext_bytes = bytes(int(binary_message[i:i+8], 2) for i in range(0, len(binary_message), 8))
            
            # Decrypt
            plaintext_bytes = crypto.decrypt(ciphertext_bytes, passphrase)
            
            # Convert plaintext back to binary string
            padded_binary_message = ''.join(format(byte, '08b') for byte in plaintext_bytes)
            
            # Read the original huffman bit length
            bit_length = int(padded_binary_message[:32], 2)
            huffman_binary = padded_binary_message[32:32+bit_length]
            logger.info("Secure pipeline decryption completed")
        else:
            huffman_binary = binary_message

        message = huffman.decode(huffman_binary)
        logger.info("Huffman decoding completed")

        return message

    except Exception as e:
        logger.error(f"Error in message decoding: {str(e)}")
        raise