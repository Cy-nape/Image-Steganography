import time
import os
import random
import string
from PIL import Image
import numpy as np

# Import project modules
from steganography.huffman import HuffmanCoding
from steganography.utils import encode_message, decode_message

def generate_text(length):
    return ''.join(random.choices(string.ascii_letters + string.digits + " ", k=length))

def test_compression():
    print("\n--- 1. Compression Rate (Huffman Coding) ---")
    huffman = HuffmanCoding()
    
    texts = {
        "Short (15 chars)": generate_text(15),
        "Paragraph (500 chars)": generate_text(500),
        "Long (2000 chars)": generate_text(2000)
    }
    
    rates = []
    for name, text in texts.items():
        original_size = len(text) * 8  # bits (assuming 8-bit ASCII)
        huffman = HuffmanCoding()
        encoded = huffman.encode(text)
        compressed_size = len(encoded)
        
        compression_rate = ((original_size - compressed_size) / original_size) * 100
        rates.append(compression_rate)
        print(f"[{name}] Original: {original_size} bits, Compressed: {compressed_size} bits -> {compression_rate:.2f}% reduction")
        
    print(f"Average Compression Rate: {sum(rates)/len(rates):.2f}%")
    print(f"Range: {min(rates):.2f}% to {max(rates):.2f}%")

def test_latency():
    print("\n--- 2. Latency/Speed ---")
    
    # Generate a test image
    img_path = "temp_test_image.png"
    out_path = "temp_test_output.png"
    Image.new('RGB', (800, 600), color='blue').save(img_path)
    
    texts = {
        "Small (50 chars)": generate_text(50),
        "Medium (500 chars)": generate_text(500),
        "Large (5000 chars)": generate_text(5000)
    }
    
    encode_times = []
    decode_times = []
    
    for name, text in texts.items():
        # Encode
        start_enc = time.time()
        _, huff = encode_message(img_path, text, output_path=out_path)
        end_enc = time.time()
        enc_time = (end_enc - start_enc) * 1000
        encode_times.append(enc_time)
        
        # Decode
        start_dec = time.time()
        decode_message(out_path, huff)
        end_dec = time.time()
        dec_time = (end_dec - start_dec) * 1000
        decode_times.append(dec_time)
        
        print(f"[{name}] Encode: {enc_time:.2f} ms | Decode: {dec_time:.2f} ms")
        
    print(f"Encode - Min: {min(encode_times):.2f} ms, Max: {max(encode_times):.2f} ms, Avg: {sum(encode_times)/len(encode_times):.2f} ms")
    print(f"Decode - Min: {min(decode_times):.2f} ms, Max: {max(decode_times):.2f} ms, Avg: {sum(decode_times)/len(decode_times):.2f} ms")
    
    # Cleanup
    if os.path.exists(img_path): os.remove(img_path)
    if os.path.exists(out_path): os.remove(out_path)

def test_scale():
    print("\n--- 3. Scale/Capacity ---")
    print("Codebase inspection in steganography/lsb.py reveals: `if len(binary_message) > img_array.size:`")
    print("This means the max capacity is 1 bit per value in the image array (which includes all channels RGB).")
    
    img_sizes = [(100, 100), (500, 500), (1920, 1080)]
    
    for w, h in img_sizes:
        capacity_bits = w * h * 3 # RGB channels
        capacity_bytes = capacity_bits / 8
        capacity_chars = capacity_bytes # rough ASCII equiv
        # We also need to subtract 32 bits for the length header
        actual_capacity_bits = capacity_bits - 32
        
        # We get an average of ~4.5 bits per char after Huffman. So:
        approx_max_chars = actual_capacity_bits / 4.5
        print(f"Image {w}x{h} (RGB): Capacity = {capacity_bits} bits (~{approx_max_chars:,.0f} chars after compression)")

if __name__ == "__main__":
    test_compression()
    test_latency()
    test_scale()
