from flask import Flask, render_template, request, jsonify, send_file, g
import os
import logging
import uuid
import hashlib
from steganography.utils import encode_message, decode_message
from extensions import db, migrate, limiter
from steganography.huffman import HuffmanCoding
import models
from auth import auth_bp, multi_auth_required
from api_keys import api_keys_bp

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, template_folder='template', static_folder='static')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', os.urandom(24))
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///app.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
migrate.init_app(app, db)
limiter.init_app(app)

app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(api_keys_bp)

import tempfile
UPLOAD_FOLDER = tempfile.gettempdir()
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

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/encode', methods=['POST'])
@multi_auth_required
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
        
        # Calculate hash of the encoded image and store huffman tree in DB
        file_hash = get_file_hash(encoded_path)
        new_job = models.EncodeJob(
            user_id=g.user.id,
            file_hash=file_hash,
            huffman_dict=huffman.huffman_dict
        )
        db.session.add(new_job)
        db.session.commit()
        logger.info(f"Stored Huffman tree for hash: {file_hash} by user: {g.user.id}")
        
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
@multi_auth_required
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
        
        job = models.EncodeJob.query.filter_by(file_hash=file_hash).first()
        if not job:
            return jsonify({'error': 'Encryption key not found for this image (Invalid or unregistered image)'}), 400
             
        huffman = HuffmanCoding()
        huffman.huffman_dict = job.huffman_dict
        
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
