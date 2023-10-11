import { useState } from 'react';
import './index.css';
import axios from 'axios';

function Home() {
  const [formData, setFormData] = useState({ url: '' });
  const [data, setData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isScrapeDone, setIsScrapeDone] = useState(false);
  const [serverMessage, setServerMessage] = useState("");
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
      setIsScrapeDone(true);
      if (response.data.error) {
        setServerMessage(response.data.error);
      }
    } catch (error) {
      console.error("Error with submission: ", error)
      setServerMessage("An error occurred while fetching data.");
      setIsLoading(false);
    } finally {
      setIsScrapeDone(true);
      setIsLoading(false);
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData({ ...formData, [name]: value })
  };

  const motorsDeals = motorsData.filter(item => item.link.includes("motors.co.uk"));
  const fbDeals = motorsData.filter(item => item.link.includes("facebook.com"));

  return (
    <div className="form-container">

      <header className="header">AutoCompare</header>
      <p className="top-info">Simply enter the URL of an AutoTrader car that you like, and we will find you better deals. For completely free.</p>
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
      {motorsDeals && motorsDeals.length > 0 && (
        <div>
          <h2>Motors Deals:</h2>
          {motorsDeals.map((item, index) => (
            <div className="motors-section" key={index}>
              
              <a href={item.link} target="_blank" rel="noopener noreferrer">
                <img src={item.thumbnail_image} alt={`Motor deal ${index + 1}`} />
              </a>
              
              <p>Price: £{item.price}</p>
              <p>Mileage: {item.mileage} miles</p>
              <p>Model: {item.model}</p>
              <p>Deal: <a href={item.link} target="_blank" rel="noopener noreferrer">{item.link}</a></p>
            </div>
          ))}
        </div>
      )}

        {isScrapeDone && (fbDeals && fbDeals.length > 0 ? (
          <div>
            <h2>Facebook Marketplace Deals:</h2>
            {fbDeals.map((item, index) => (
              <div className="fb-section" key={index}>
                
                <a href={item.link} target="_blank" rel="noopener noreferrer">
                  <img src={item.image} className="scraped-car-img" alt={`Facebook Deal ${index + 1}`} />
                </a>
                
                <p>Price: £{item.price}</p>
                <p>Mileage: {item.mileage} mileage</p>
                <p>Model: {item.model}</p>
                <p>Deal: <a href={item.link} target="_blank" rel="noopener noreferrer">{item.link}</a></p>
            </div>
          ))}
        </div>
      ) : (
        <div>
          <h2>Facebook Marketplace Deals</h2>
          <p>No deals are available from Facebook Marketplace.</p>
          {serverMessage && <div className="server-message">{serverMessage}</div>}

        </div>
      ))}

    </div>
  );
}

export default Home;
