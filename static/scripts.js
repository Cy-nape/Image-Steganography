// scripts.js
document.addEventListener("DOMContentLoaded", function () {
    let jwtToken = localStorage.getItem('jwt');
    
    // Redirect to login if no token is found
    if (!jwtToken) {
        window.location.href = '/login';
        return;
    }

    function getAuthHeaders() {
        return {
            'Authorization': 'Bearer ' + jwtToken,
            'Content-Type': 'application/json'
        };
    }

    // Load initial data
    loadApiKeys();

    // Logout logic
    const btnLogout = document.getElementById('btn-logout');
    if (btnLogout) {
        btnLogout.addEventListener('click', () => {
            localStorage.removeItem('jwt');
            window.location.href = '/login';
        });
    }

    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');

    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const tabId = btn.getAttribute('data-tab');
            
            // Update active states
            tabBtns.forEach(b => b.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));
            
            btn.classList.add('active');
            if (tabId === 'encode') {
                document.getElementById('encoding-section').classList.add('active');
            } else if (tabId === 'decode') {
                document.getElementById('decoding-section').classList.add('active');
            } else if (tabId === 'keys') {
                document.getElementById('keys-section').classList.add('active');
                if(jwtToken) loadApiKeys();
            }
        });
    });

    // File Preview Logic
    function setupFilePreview(inputId, previewClass) {
        const input = document.getElementById(inputId);
        const preview = input.parentElement.querySelector('.file-preview');

        input.addEventListener('change', function(e) {
            preview.innerHTML = '';
            preview.classList.remove('active'); // Reset animation
            const file = e.target.files[0];
            
            if (file && file.type.startsWith('image/')) {
                const img = document.createElement('img');
                img.src = URL.createObjectURL(file);
                preview.appendChild(img);
                // Small timeout to allow browser to register the removal of class for re-animation
                setTimeout(() => {
                    preview.classList.add('active');
                }, 10);
            }
        });
    }

    setupFilePreview('image', '.file-preview');
    setupFilePreview('decode-image', '.file-preview');

    // Character Counter
    const messageInput = document.getElementById('message');
    const charCount = document.getElementById('char-count');

    messageInput.addEventListener('input', function() {
        charCount.textContent = this.value.length;
    });

    // Encode Form Submission
    document.getElementById("encode-form").addEventListener("submit", async function (e) {
        e.preventDefault();
        const loader = document.getElementById("encoding-loader");
        const downloadSection = document.getElementById("download-link");

        try {
            loader.style.display = "block";
            downloadSection.style.display = "none";

            const formData = new FormData();
            formData.append("image", document.getElementById("image").files[0]);
            formData.append("message", document.getElementById("message").value);

            // We must remove Content-Type from getAuthHeaders because fetch automatically 
            // sets it with the correct boundary for multipart/form-data when passing FormData.
            const headers = getAuthHeaders();
            delete headers['Content-Type'];

            const response = await fetch("/encode", {
                method: "POST",
                headers: headers,
                body: formData
            });

            if (response.ok) {
                const blob = await response.blob();
                const downloadLink = document.getElementById("encoded-download");
                downloadLink.href = URL.createObjectURL(blob);
                downloadLink.download = "encoded_image.png";
                downloadSection.style.display = "block";
            } else {
                const error = await response.json();
                alert(error.error || "Encoding failed. Please try again.");
            }
        } catch (error) {
            console.error("Error:", error);
            alert("An error occurred during encoding.");
        } finally {
            loader.style.display = "none";
        }
    });

    // Decode Form Submission
    document.getElementById("decode-form").addEventListener("submit", async function (e) {
        e.preventDefault();
        const formData = new FormData();
        formData.append("image", document.getElementById("decode-image").files[0]);
    
        try {
            const headers = getAuthHeaders();
            delete headers['Content-Type'];

            const response = await fetch("/decode", {
                method: "POST",
                headers: headers,
                body: formData
            });
            
            if (response.ok) {
                const result = await response.json();
                if (result.error) {
                    alert(result.error);
                } else {
                    document.getElementById("message-output").textContent = result.message;
                    document.getElementById("decoded-message").style.display = "block";
                }
            } else {
                alert("Decoding failed. Please check your inputs and try again.");
            }
        } catch (error) {
            console.error("Error:", error);
            alert("An error occurred during decoding.");
        }
    });

    // Copy Decoded Message
    document.getElementById("copy-message").addEventListener("click", function() {
        const messageText = document.getElementById("message-output").textContent;
        navigator.clipboard.writeText(messageText).then(() => {
            this.textContent = "Copied!";
            setTimeout(() => {
                this.textContent = "Copy";
            }, 2000);
        });
    });

    // Auth logic has been moved to static/login.js

    // API Keys logic
    document.getElementById('btn-generate-key').addEventListener('click', async () => {
        const res = await fetch('/api-keys', {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({})
        });
        if (res.ok) {
            const data = await res.json();
            document.getElementById('new-key-value').textContent = data.key;
            document.getElementById('new-key-display').style.display = 'block';
            loadApiKeys();
        } else {
            alert('Failed to generate key');
        }
    });

    async function loadApiKeys() {
        const res = await fetch('/api-keys', { headers: getAuthHeaders() });
        if (res.ok) {
            const data = await res.json();
            const list = document.getElementById('keys-list');
            list.innerHTML = '';
            data.api_keys.forEach(k => {
                const div = document.createElement('div');
                div.style.marginBottom = '10px';
                div.innerHTML = `
                    <strong>${k.prefix}...</strong> (${k.label}) 
                    <button class="btn-secondary revoke-btn" data-id="${k.id}" style="padding: 2px 5px; font-size: 12px; margin-left: 10px;">Revoke</button>
                `;
                list.appendChild(div);
            });
            
            document.querySelectorAll('.revoke-btn').forEach(btn => {
                btn.addEventListener('click', async (e) => {
                    const id = e.target.getAttribute('data-id');
                    await fetch('/api-keys/' + id, { method: 'DELETE', headers: getAuthHeaders() });
                    loadApiKeys();
                });
            });
        }
    }
});