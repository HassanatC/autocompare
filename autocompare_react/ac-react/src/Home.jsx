import { useState } from 'react';
import './index.css';
import axios from 'axios';

function Home() {
  const [formData, setFormData] = useState({ url: '' });
  const [data, setData] = useState(null);
  const [motorsData, setMotorsData] = useState([]);


  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const response = await axios.post('http://localhost:8000/scrape/', formData, {
        headers: {
          'Content-Type': 'application/json',
        },
      });
      setData(response.data.data);
      setMotorsData(response.data.motors_data);
    } catch (error) {
      console.error("Error with submission: ", error)
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData({ ...formData, [name]: value })
  };

  return (
    <div>
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          name="url"
          value={formData.url}
          onChange={handleChange}
          placeholder="Enter the car URL.."
        />
        <button type="submit">Submit</button>
      </form>

      {data && (
              <div>
                <h2>Data:</h2>
                <p>Car Price: {data.price}</p>
                <p>Car Brand: {data.brand}</p>
              </div>
            )}

            {motorsData && motorsData.length > 0 && (
              <div>
                <h2>Motors Data:</h2>
                {motorsData.map((item, index) => (
                  <div key={index}>
                    <p>Other car Price: {item.price}</p>
                    <p>Other car Mileage: {item.mileage}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        );
      }

export default Home
