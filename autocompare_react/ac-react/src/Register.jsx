import './index.css';

function Register() {
    return (
        <div className="form-container">
            <div className="header">Register</div>
            <p className="top-info">Register today, and start to save all searches and unlock enhanced featuers.</p>
            <form className="url-form">
                <label>
                    <p>Username:</p>
                    <input type="text" placeholder="Enter your username" required />
                </label>
                <label>
                    <p>E-mail:</p>
                    <input type="email" placeholder="Enter your email" required />
                </label>
                <label>
                    <p>Enter a secure password:</p>
                    <input type="password" placeholder="Enter your password" required />
                </label>
                <label>
                    <p>Confirm your password:</p>
                    <input type="password" placeholder="Confirm your password" required />
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