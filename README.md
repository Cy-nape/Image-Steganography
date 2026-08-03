# Image Steganography Project

A Flask-based Image Steganography API demonstrating applied cryptography, secure API design, and full-stack engineering. Secret messages are hidden inside images using a layered security pipeline combining Huffman compression, AES-256-GCM encryption, and LSB bit embedding.

---

## What is Steganography?

Steganography is the art of hiding data *within* data. A secret message (text) is embedded inside an innocent-looking image — invisible to the naked eye and undetectable without the correct passphrase and decoding key.

---

## Security Architecture (Three Layers)

### 1. Huffman Coding — Compression
The message is compressed before embedding. Characters that appear frequently get short binary codes; rare characters get longer ones. This minimises the number of LSB pixels that need to be modified, reducing the visual footprint in the carrier image.

### 2. AES-256-GCM Encryption (Secure Pipeline)
When the secure pipeline is selected, the compressed message is encrypted using **AES-256-GCM** (Authenticated Encryption with Associated Data):
- A fresh 16-byte **salt** and 12-byte **nonce** are generated via `os.urandom()` for every encode call — guaranteeing ciphertext uniqueness even for identical inputs.
- The passphrase is stretched into a 256-bit AES key using **PBKDF2-HMAC-SHA256 with 100,000 iterations**, making brute-force attacks computationally expensive.
- The GCM authentication tag detects any tampering: a single flipped bit in the image causes decryption to raise a `DecryptionError`.

### 3. LSB (Least Significant Bit) Embedding
Every pixel has Red, Green, and Blue channels — each an 8-bit integer (0–255). Changing only the least significant bit causes a colour shift of ±1, imperceptible to human vision. The binary payload (flag + length header + message) is embedded into the LSBs of the flattened pixel array:

```
Original:  1001011[0]  (Dark Red, value 150)
Modified:  1001011[1]  (Still Dark Red, value 151 — but now carries a secret bit)
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python / Flask |
| Cryptography | `cryptography` (AES-GCM, PBKDF2) |
| Image Processing | Pillow (PIL), NumPy |
| Database | SQLite / PostgreSQL via SQLAlchemy |
| Migrations | Flask-Migrate (Alembic) |
| Authentication | JWT Bearer tokens + hashed API Keys |
| Rate Limiting | Flask-Limiter |
| Frontend | HTML / CSS / Vanilla JS (glassmorphism UI) |

---

## API Security Design

### Dual-Auth System
The `/encode` and `/decode` routes are protected by `@multi_auth_required`, which accepts **either**:
- **JWT Bearer token** — issued at login, for web sessions. Verified with `HS256` against the server's `SECRET_KEY`.
- **API Key** — a `secrets.token_hex(32)` key, stored only as a SHA-256 hash in the database. The raw key is shown once on creation. Supports soft-delete revocation (`is_active=False`).

### Huffman Dictionary Storage
Because the Huffman codebook is required for decoding, it is stored as JSON in the `encode_jobs` table, keyed by the **SHA-256 hash** of the output encoded image. This survives server restarts and ties the decoding key to the exact pixel state of the image.

### File Upload Hardening
1. Extension allowlist: `{.png, .jpg, .jpeg, .bmp}`
2. PIL `verify()` after saving — detects executables renamed to `.png`.
3. Encoded output is written to an in-memory `io.BytesIO()` buffer — **zero disk artefacts** from encoded images.
4. Temporary input files are deleted in a `finally:` block even on exceptions.

---

## How to Run

```bash
# 1. Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Initialise the database
flask db upgrade

# 4. Start the server
python app.py
```

Open `http://127.0.0.1:5000` in your browser. Register an account, then use the **Encode** tab to embed a secret message into an image, and the **Decode** tab to recover it.

---

## Running Tests

```bash
pytest tests/ -v
```

The test suite covers:
- AES-GCM encrypt/decrypt round-trips
- Wrong passphrase and tampered ciphertext rejection
- Full encode → decode workflow via both JWT and API Key auth
- Basic and Secure pipeline end-to-end
- User isolation (User B cannot access User A's keys or jobs)
- API key revocation and subsequent rejection
- RGBA image handling (alpha channel stripping)

---

## Known Limitations

- **Stateless Decoding:** The Huffman dictionary is stored locally keyed by the output image's SHA-256 hash. An encoded image cannot be decoded on a different server instance, or after the image is re-compressed (which changes its hash).
- **Format Fragility:** LSB steganography is extremely fragile. Uploading a stego-image to WhatsApp, Twitter, or any service that re-encodes images with lossy compression will destroy the payload entirely.
- **Capacity Constraint:** Exactly 1 bit per colour channel pixel is available. Capacity = `(width × height × 3) - 40` bits (the 40-bit header overhead for pipeline flag + message length).
- **RGBA Images:** All images are converted to RGB before embedding. Any existing alpha channel (transparency) is stripped in the output PNG.
- **Synchronous DoS Risk:** Image processing is synchronous. Very large images could tie up worker threads; the existing Flask-Limiter rate limiting partially mitigates this.

---

## Project History

The project originally included a **spread-spectrum obfuscation layer** (`spread_spectrum.py`) as a second line of defence after Huffman compression. The implementation XOR-spread message bits across the pixel array using a pseudorandom sequence seeded with a fixed integer (`random.seed(42)`).

After a security review, this approach was identified as **cryptographically weak**:
- The fixed seed made the XOR sequence fully deterministic and reproducible by any attacker who read the source code.
- XOR with a known sequence provides zero confidentiality — it is security-by-obscurity, not encryption.

The spread-spectrum layer was **replaced with AES-256-GCM authenticated encryption** (`steganography/crypto.py`), which provides:
- **Confidentiality** via a fresh random salt + nonce per encoding operation.
- **Integrity and authenticity** via GCM's authentication tag — any bit-flip in the stego-image is detected on decode.
- **Key hardening** via PBKDF2-HMAC-SHA256 with 100,000 iterations, making brute-force attacks computationally expensive.

The old `spread_spectrum.py` file has been removed. Its migration out of the codebase is documented here so the design decision is not lost.
