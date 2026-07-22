import os
import time
import argparse
import random
import string
import csv
import math
import numpy as np
from PIL import Image

# Import existing modules
from app import app, db
from models import ExperimentRun
from steganography.huffman import HuffmanCoding
from steganography.lsb import lsb_encode, lsb_decode
from steganography.spread_spectrum import spread_spectrum_encode, spread_spectrum_decode

def mse(imageA, imageB):
    err = np.sum((imageA.astype("float") - imageB.astype("float")) ** 2)
    err /= float(imageA.shape[0] * imageA.shape[1] * imageA.shape[2])
    return err

def psnr(imageA, imageB):
    mse_val = mse(imageA, imageB)
    if mse_val == 0:
        return 100
    PIXEL_MAX = 255.0
    return 20 * math.log10(PIXEL_MAX / math.sqrt(mse_val))

def generate_text(length):
    chars = string.ascii_letters + string.digits + " ,.!?\n"
    return ''.join(random.choices(chars, k=length))

def run_experiment(img_path, message_length):
    results = []
    
    filename = os.path.basename(img_path)
    img_size_kb = os.path.getsize(img_path) / 1024.0
    with Image.open(img_path) as img:
        width, height = img.size
        # Capacity (rough estimate): 1 pixel can store 3 bits (R, G, B) for LSB. Total pixels = w * h. Total bits = w * h * 3.
        img_capacity_bits = width * height * 3

    # Generate message
    message = generate_text(message_length)
    
    # 1. LSB (Huffman Compressed)
    alg1_name = "LSB (Huffman Compressed)"
    try:
        t0 = time.time()
        huffman = HuffmanCoding()
        binary_message = huffman.encode(message)
        comp_ratio = len(binary_message) / (message_length * 8)
        
        message_bits = len(binary_message)
        if message_bits > img_capacity_bits:
            raise ValueError(f"Message too large for image capacity ({message_bits} > {img_capacity_bits})")
            
        out_path1 = "tmp_alg1.png"
        lsb_encode(img_path, binary_message, message_bits, out_path1)
        encode_time_ms = (time.time() - t0) * 1000
        
        t1 = time.time()
        decoded_bin = lsb_decode(out_path1)
        decoded_msg = huffman.decode(decoded_bin)
        decode_time_ms = (time.time() - t1) * 1000
        
        # Calculate PSNR
        orig_arr = np.array(Image.open(img_path).convert('RGB'))
        encoded_arr = np.array(Image.open(out_path1).convert('RGB'))
        p_val = psnr(orig_arr, encoded_arr)
        
        results.append({
            "image_name": filename, "image_size_kb": img_size_kb, "width": width, "height": height,
            "algorithm": alg1_name, "message_length": message_length, "compression_ratio": comp_ratio,
            "encode_time_ms": encode_time_ms, "decode_time_ms": decode_time_ms, "psnr": p_val, "success": True
        })
        if os.path.exists(out_path1): os.remove(out_path1)
    except Exception as e:
        print(f"[{alg1_name}] Failed for {filename} length {message_length}: {e}")
        results.append({
            "image_name": filename, "image_size_kb": img_size_kb, "width": width, "height": height,
            "algorithm": alg1_name, "message_length": message_length, "compression_ratio": None,
            "encode_time_ms": None, "decode_time_ms": None, "psnr": None, "success": False
        })

    # 2. Spread Spectrum (Huffman Compressed)
    alg2_name = "Spread Spectrum (Huffman Compressed)"
    try:
        t0 = time.time()
        huffman2 = HuffmanCoding()
        binary_message = huffman2.encode(message)
        comp_ratio = len(binary_message) / (message_length * 8)
        
        spread_msg = spread_spectrum_encode(binary_message, len(binary_message))
        message_bits = len(spread_msg)
        if message_bits > img_capacity_bits:
            raise ValueError(f"Message too large for image capacity ({message_bits} > {img_capacity_bits})")
            
        out_path2 = "tmp_alg2.png"
        lsb_encode(img_path, spread_msg, message_bits, out_path2)
        encode_time_ms = (time.time() - t0) * 1000
        
        t1 = time.time()
        decoded_spread = lsb_decode(out_path2)
        decoded_bin = spread_spectrum_decode(decoded_spread, len(decoded_spread))
        decoded_msg = huffman2.decode(decoded_bin)
        decode_time_ms = (time.time() - t1) * 1000
        
        orig_arr = np.array(Image.open(img_path).convert('RGB'))
        encoded_arr = np.array(Image.open(out_path2).convert('RGB'))
        p_val = psnr(orig_arr, encoded_arr)
        
        results.append({
            "image_name": filename, "image_size_kb": img_size_kb, "width": width, "height": height,
            "algorithm": alg2_name, "message_length": message_length, "compression_ratio": comp_ratio,
            "encode_time_ms": encode_time_ms, "decode_time_ms": decode_time_ms, "psnr": p_val, "success": True
        })
        if os.path.exists(out_path2): os.remove(out_path2)
    except Exception as e:
        print(f"[{alg2_name}] Failed for {filename} length {message_length}: {e}")
        results.append({
            "image_name": filename, "image_size_kb": img_size_kb, "width": width, "height": height,
            "algorithm": alg2_name, "message_length": message_length, "compression_ratio": None,
            "encode_time_ms": None, "decode_time_ms": None, "psnr": None, "success": False
        })
        
    return results

def main():
    parser = argparse.ArgumentParser(description="Generate dataset of steganography experiment runs.")
    parser.add_argument('--img-dir', type=str, required=True, help="Directory containing sample images")
    parser.add_argument('--csv-out', type=str, default="results.csv", help="Path to output CSV file")
    args = parser.parse_args()
    
    if not os.path.exists(args.img_dir):
        print(f"Directory {args.img_dir} does not exist.")
        return
        
    images = [os.path.join(args.img_dir, f) for f in os.listdir(args.img_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    if not images:
        print(f"No PNG/JPG images found in {args.img_dir}.")
        return
        
    print(f"Found {len(images)} images to process.")
    
    lengths = [10, 50, 100, 500, 1000, 5000]
    all_results = []
    
    # Initialize CSV if not exists, else we can overwrite or append. Let's overwrite for idempotency.
    fieldnames = ["image_name", "image_size_kb", "width", "height", "algorithm", "message_length", 
                  "compression_ratio", "encode_time_ms", "decode_time_ms", "psnr", "success"]
                  
    total_runs = len(images) * len(lengths)
    current_run = 0
    
    with app.app_context():
        # Clear previous experiment runs (optional, but good for idempotency)
        db.session.query(ExperimentRun).delete()
        db.session.commit()
        
        with open(args.csv_out, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for img_path in images:
                for length in lengths:
                    current_run += 1
                    print(f"[{current_run}/{total_runs}] Processing {os.path.basename(img_path)} with message length {length}...")
                    
                    results = run_experiment(img_path, length)
                    
                    for r in results:
                        writer.writerow(r)
                        all_results.append(r)
                        
                        # Save to DB
                        run_record = ExperimentRun(
                            image_name=r['image_name'],
                            image_size_kb=r['image_size_kb'],
                            width=r['width'],
                            height=r['height'],
                            algorithm=r['algorithm'],
                            message_length=r['message_length'],
                            compression_ratio=r['compression_ratio'],
                            encode_time_ms=r['encode_time_ms'],
                            decode_time_ms=r['decode_time_ms'],
                            psnr=r['psnr'],
                            success=r['success']
                        )
                        db.session.add(run_record)
                    
                    # Commit per image/length to save progress
                    db.session.commit()
                    
    print(f"Done! Results written to {args.csv_out} and the experiment_runs database table.")

if __name__ == "__main__":
    main()
