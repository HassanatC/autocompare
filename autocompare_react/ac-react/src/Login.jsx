import './index.css';

function Login() {
    return (
        <div className="form-container">
            <div className="header">Login</div>
            <form className="url-form">
                <label>
                    <p>Email:</p>
                    <input type="email" placeholder="Enter your email" required />
                </label>
                <label>
                    <p>Password:</p>
                    <input type="password" placeholder="Enter your password" required />
                </label>
                <button type="submit">Login</button>
            </form>
            <p>
                Don't have an account? <a href="/register" style={{ color: 'var(--primary-color)' }}>Register</a>
            </p>
        </div>
    );
}

export default Login;