import { Link } from 'react-router-dom';

export default function Nav() {
  return (
    <>
      <nav className="navbar">
        <ul>
          <li><Link to="/">Home</Link></li>
        </ul>
      </nav>

    </>
  );
}
