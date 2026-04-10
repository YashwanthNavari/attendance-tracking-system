function setRole(role) {
    document.querySelectorAll('.role-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelector(`.role-btn[onclick="setRole('${role}')"]`).classList.add('active');
    document.getElementById('role').value = role;
}

async function handleLogin(event) {
    event.preventDefault();

    const username = document.getElementById('username').value;
    const role = document.getElementById('role').value;

    // In a real app, password should be sent.
    try {
        const response = await fetch('/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username, role }) // Simple login for prototype
        });

        const data = await response.json();

        if (response.ok) {
            if (data.role === 'faculty') {
                window.location.href = '/faculty_dashboard';
            } else {
                window.location.href = '/student_dashboard';
            }
        } else {
            alert(data.message || 'Login failed');
        }
    } catch (error) {
        console.error('Login error:', error);
        alert('An error occurred during login');
    }
}
