import './index.css';

function Register() {
    return (
        <div className="form-container">
            <div className="header">Register</div>
            <form className="url-form">
                <label>
                    <p>Name:</p>
                    <input type="text" placeholder="Enter your name" required />
                </label>
                <label>
                    <p>Email:</p>
                    <input type="email" placeholder="Enter your email" required />
                </label>
                <label>
                    <p>Password:</p>
                    <input type="password" placeholder="Enter your password" required />
                </label>
                <button type="submit">Register</button>
            </form>
            <p>
                Already have an account? <a href="/login" style={{ color: 'var(--primary-color)' }}>Login</a>
            </p>
        </div>
    );
}

export default Register;