import { useState } from 'react';
import './index.css';
import axios from 'axios';

function Home() {
  const [formData, setFormData] = useState({ url: '' });
  const [data, setData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [motorsData, setMotorsData] = useState([]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    // axios
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
      setIsLoading(false);
    } finally {
      setIsLoading(false);
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData({ ...formData, [name]: value })
  };

  return (
    <div className="form-container">
      <form className="url-form" onSubmit={handleSubmit}>
        <input
          type="text"
          name="url"
          value={formData.url}
          onChange={handleChange}
          placeholder="Enter the car URL.."
        />
        <button type="submit" disabled={isLoading}>Submit</button>
      </form>

      {isLoading && (
        <div className="loading-text">
          <p>Please wait while we fetch relevant deals!</p>
        </div>
      )}

      {data && (
              <div className="data-section">
                <h2>Your Chosen Car:</h2>
                <img src={data.image_url} className="scraped-car-img" alt="Car" />
                <p>Car Price: {data.price}</p>
                <p>Car Brand: {data.brand}</p>
                <p>Car Registration: {data.registration}</p>
                <p>Car Mileage: {data.mileage} </p>
                <p>Previous Owners: {data.previous_owners}</p>
              </div>
            )}

          {/*renders the list of suggested motors*/}
            {motorsData && motorsData.length > 0 && (
              <div>
                <h2>Motors Deals:</h2>
                {motorsData.map((item, index) => (
                  <div className="motors-section" key={index}>
                    <img src={item.thumbnail_image}></img>
                    <p>Price: £{item.price}</p>
                    <p>Mileage: {item.mileage} miles</p>
                    <p>Deal: <a href={item.link} target="_blank" rel="noopener noreferrer">{item.link}</a></p>
                  </div>
                ))}
              </div>
            )}
          </div>
        );
      }

export default Home
