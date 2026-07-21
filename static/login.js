document.addEventListener('DOMContentLoaded', () => {
    const authStatus = document.getElementById('auth-status');
    const form = document.getElementById('auth-form');
    
    // If already logged in, redirect to home
    if (localStorage.getItem('jwt')) {
        window.location.href = '/';
        return;
    }

    form.addEventListener('submit', async (e) => {
        e.preventDefault(); // Handle login on submit
        const email = document.getElementById('email').value;
        const password = document.getElementById('password').value;
        
        authStatus.style.color = 'black';
        authStatus.textContent = 'Logging in...';
        
        try {
            const res = await fetch('/auth/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password })
            });
            const data = await res.json();
            if (res.ok) {
                localStorage.setItem('jwt', data.token);
                authStatus.style.color = 'green';
                authStatus.textContent = 'Logged in successfully! Redirecting...';
                setTimeout(() => { window.location.href = '/'; }, 500);
            } else {
                authStatus.style.color = 'red';
                authStatus.textContent = data.error || 'Login failed';
            }
        } catch (e) {
            authStatus.style.color = 'red';
            authStatus.textContent = 'Network error during login';
        }
    });

    document.getElementById('btn-register').addEventListener('click', async () => {
        // We use click here so we don't trigger native HTML5 validation unless we want to,
        // but we should validate first.
        const email = document.getElementById('email').value;
        const password = document.getElementById('password').value;
        
        if(!email || !password) {
            authStatus.style.color = 'red';
            authStatus.textContent = 'Email and password are required to register.';
            return;
        }

        authStatus.style.color = 'black';
        authStatus.textContent = 'Registering...';
        
        try {
            const res = await fetch('/auth/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password })
            });
            const data = await res.json();
            if (res.ok) {
                authStatus.style.color = 'green';
                authStatus.textContent = 'Registered successfully! You can now log in.';
            } else {
                authStatus.style.color = 'red';
                authStatus.textContent = data.error || 'Registration failed';
            }
        } catch (e) {
            authStatus.style.color = 'red';
            authStatus.textContent = 'Network error during registration';
        }
    });
});
