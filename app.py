from flask import Flask, render_template, request, jsonify, send_file, g
import os
import logging
import uuid
import hashlib
import io
from PIL import Image
from steganography.crypto import DecryptionError
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
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-12345')
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
    try:
        if 'image' not in request.files or 'message' not in request.form:
            return jsonify({'error': 'Missing image or message'}), 400
        
        image = request.files['image']
        message = request.form['message']
        pipeline = request.form.get('pipeline', 'secure')
        passphrase = request.form.get('passphrase')
        
        if image.filename == '':
            return jsonify({'error': 'No selected file'}), 400
            
        # Validate extension
        allowed_extensions = {'.png', '.jpg', '.jpeg', '.bmp'}
        ext = os.path.splitext(image.filename)[1].lower()
        if ext not in allowed_extensions:
            return jsonify({'error': 'Invalid file extension'}), 400
            
        # Create unique filenames
        unique_id = str(uuid.uuid4())
        temp_input = os.path.join(UPLOAD_FOLDER, f"input_{unique_id}.png")
        
        # Save input image
        image.save(temp_input)
        
        # Verify image using PIL
        try:
            with Image.open(temp_input) as img:
                img.verify()
        except Exception:
            return jsonify({'error': 'Invalid image file'}), 400
        
        # Encode message to an in-memory buffer
        output_buffer = io.BytesIO()
        _, huffman = encode_message(
            temp_input, 
            message, 
            output_path=output_buffer, 
            pipeline=pipeline, 
            passphrase=passphrase
        )
        
        # Calculate hash of the encoded image buffer
        output_buffer.seek(0)
        file_hash = hashlib.sha256(output_buffer.read()).hexdigest()
        output_buffer.seek(0)
        
        # Store huffman tree in DB
        new_job = models.EncodeJob(
            user_id=g.user.id,
            file_hash=file_hash,
            huffman_dict=huffman.huffman_dict,
            pipeline=pipeline
        )
        db.session.add(new_job)
        db.session.commit()
        logger.info(f"Stored Huffman tree for hash: {file_hash} by user: {g.user.id}")
        
        return send_file(output_buffer, as_attachment=True, download_name='encoded_image.png', mimetype='image/png')

    except ValueError as e:
        logger.error(f"Encoding error: {str(e)}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Encoding error: {str(e)}")
        return jsonify({'error': str(e)}), 500
        
    finally:
        if temp_input and os.path.exists(temp_input):
            os.remove(temp_input)

@app.route('/decode', methods=['POST'])
@multi_auth_required
def decode():
    temp_input = None
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'Missing image'}), 400
            
        image = request.files['image']
        passphrase = request.form.get('passphrase')
        
        if image.filename == '':
            return jsonify({'error': 'No selected file'}), 400
            
        # Validate extension
        allowed_extensions = {'.png', '.jpg', '.jpeg', '.bmp'}
        ext = os.path.splitext(image.filename)[1].lower()
        if ext not in allowed_extensions:
            return jsonify({'error': 'Invalid file extension'}), 400
            
        unique_id = str(uuid.uuid4())
        temp_input = os.path.join(UPLOAD_FOLDER, f"decode_{unique_id}.png")
        image.save(temp_input)
        
        # Verify image
        try:
            with Image.open(temp_input) as img:
                img.verify()
        except Exception:
            return jsonify({'error': 'Invalid image file'}), 400
        
        # Calculate hash to find matching Huffman tree
        file_hash = get_file_hash(temp_input)
        logger.info(f"Looking up Huffman tree for hash: {file_hash}")
        
        job = models.EncodeJob.query.filter_by(file_hash=file_hash).first()
        if not job:
            return jsonify({'error': 'Encryption key not found for this image (Invalid or unregistered image)'}), 400
             
        huffman = HuffmanCoding()
        huffman.huffman_dict = job.huffman_dict
        
        decoded_message = decode_message(temp_input, huffman, passphrase=passphrase)
        
        return jsonify({'message': decoded_message})

    except DecryptionError as e:
        logger.error(f"Decryption error: {str(e)}")
        return jsonify({'error': str(e)}), 400
    except ValueError as e:
        logger.error(f"Value error: {str(e)}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Decoding error: {str(e)}")
        return jsonify({'error': str(e)}), 500
        
    finally:
        if temp_input and os.path.exists(temp_input):
            os.remove(temp_input)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
