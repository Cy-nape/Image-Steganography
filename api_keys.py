from flask import Blueprint, request, jsonify, g
from extensions import db
from models import ApiKey
from auth import token_required
import secrets
import hashlib

api_keys_bp = Blueprint('api_keys', __name__)

@api_keys_bp.route('/api-keys', methods=['POST'])
@token_required
def create_api_key():
    data = request.get_json() or {}
    label = data.get('label', 'Default Key')

    # Generate a cryptographically secure 32-byte hex string (64 characters)
    raw_key = secrets.token_hex(32)
    
    # Hash for storage
    key_hash = hashlib.sha256(raw_key.encode('utf-8')).hexdigest()
    
    # Prefix for display
    key_prefix = raw_key[:8]

    new_key = ApiKey(
        user_id=g.user.id,
        key_hash=key_hash,
        key_prefix=key_prefix,
        label=label
    )
    db.session.add(new_key)
    db.session.commit()

    return jsonify({
        'message': 'API Key created successfully',
        'key': raw_key,  # ONLY SHOWN ONCE
        'id': new_key.id,
        'prefix': key_prefix,
        'label': label
    }), 201

@api_keys_bp.route('/api-keys', methods=['GET'])
@token_required
def list_api_keys():
    keys = ApiKey.query.filter_by(user_id=g.user.id, is_active=True).all()
    return jsonify({
        'api_keys': [{
            'id': k.id,
            'prefix': k.key_prefix,
            'label': k.label,
            'created_at': k.created_at.isoformat(),
            'last_used_at': k.last_used_at.isoformat() if k.last_used_at else None
        } for k in keys]
    }), 200

@api_keys_bp.route('/api-keys/<int:key_id>', methods=['DELETE'])
@token_required
def revoke_api_key(key_id):
    # Ensure the key belongs to the current user
    key = ApiKey.query.filter_by(id=key_id, user_id=g.user.id).first()
    if not key:
        return jsonify({'error': 'API Key not found or access denied'}), 404

    # Soft delete
    key.is_active = False
    db.session.commit()

    return jsonify({'message': 'API Key revoked successfully'}), 200
