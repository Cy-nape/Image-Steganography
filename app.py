from flask import Flask, render_template, request, jsonify, send_file
import os
import logging
import uuid
import hashlib
from steganography.utils import encode_message, decode_message

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, template_folder='template', static_folder='static')
app.secret_key = os.urandom(24)

# Store Huffman trees in memory using image hash as key
# Key: SHA256 hash of the encoded image
# Value: HuffmanCoding object
HUFFMAN_STORE = {}

UPLOAD_FOLDER = 'image'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def get_file_hash(file_path):
    """Calculate SHA256 hash of a file"""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read and update hash string value in blocks of 4K
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/encode', methods=['POST'])
def encode():
    temp_input = None
    temp_output = None
    try:
        if 'image' not in request.files or 'message' not in request.form:
            return jsonify({'error': 'Missing image or message'}), 400
        
        image = request.files['image']
        message = request.form['message']
        
        if image.filename == '':
            return jsonify({'error': 'No selected file'}), 400
            
        # Create unique filenames
        unique_id = str(uuid.uuid4())
        temp_input = os.path.join(UPLOAD_FOLDER, f"input_{unique_id}.png")
        temp_output = os.path.join(UPLOAD_FOLDER, f"encoded_{unique_id}.png")
        
        # Save input image
        image.save(temp_input)
        
        # Encode message
        encoded_path, huffman = encode_message(temp_input, message, output_path=temp_output)
        
        # Calculate hash of the encoded image and store huffman tree
        file_hash = get_file_hash(encoded_path)
        HUFFMAN_STORE[file_hash] = huffman
        logger.info(f"Stored Huffman tree for hash: {file_hash}")
        
        return send_file(encoded_path, as_attachment=True, download_name='encoded_image.png')

    except Exception as e:
        logger.error(f"Encoding error: {str(e)}")
        return jsonify({'error': str(e)}), 500
        
    finally:
        # Cleanup input file, keep output file until sent? 
        # send_file might need it. Flask handles file handle but we manually delete?
        # send_file with as_attachment=True opens the file. We shouldn't delete immediately.
        # But we can assume Flask serves it quickly. 
        # For simplicity in this fix, we will leave the files in 'image' folder or clean up inputs.
        if temp_input and os.path.exists(temp_input):
            os.remove(temp_input)
        # We perform lazy cleanup of output files or rely on OS/user to clean image folder
        # Actually, let's not delete output file immediately as send_file needs it.

@app.route('/decode', methods=['POST'])
def decode():
    temp_input = None
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'Missing image'}), 400
            
        image = request.files['image']
        if image.filename == '':
            return jsonify({'error': 'No selected file'}), 400
            
        unique_id = str(uuid.uuid4())
        temp_input = os.path.join(UPLOAD_FOLDER, f"decode_{unique_id}.png")
        image.save(temp_input)
        
        # Calculate hash to find matching Huffman tree
        file_hash = get_file_hash(temp_input)
        logger.info(f"Looking up Huffman tree for hash: {file_hash}")
        
        if file_hash not in HUFFMAN_STORE:
             # Fallback: Try decoding with ONLY the latest huffman if store has 1 item? 
             # Or just fail.
             # Ideally we fail.
             if not HUFFMAN_STORE:
                 return jsonify({'error': 'No Huffman keys stored. Server restarted?'}), 400
             # Maybe the hash is different because of metadata/filename changes?
             # PNG content shouldn't change.
             # Let's try to search? No, strictly match for now.
             
             # Wait, maybe the user tries to decode an image produced BEFORE the server restart?
             # In that case, we can't recover.
             return jsonify({'error': 'Encryption key not found for this image (Session expired or server restarted)'}), 400
             
        huffman = HUFFMAN_STORE[file_hash]
        
        decoded_message = decode_message(temp_input, huffman)
        
        return jsonify({'message': decoded_message})

    except Exception as e:
        logger.error(f"Decoding error: {str(e)}")
        return jsonify({'error': str(e)}), 500
        
    finally:
        if temp_input and os.path.exists(temp_input):
            os.remove(temp_input)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
