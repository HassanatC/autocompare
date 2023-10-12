import { useState } from 'react';
import './index.css';
import axios from 'axios';

function Home() {
  const [formData, setFormData] = useState({ url: '' });
  const [data, setData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isScrapeDone, setIsScrapeDone] = useState(false);
  const [serverMessage, setServerMessage] = useState("");
  const [fbData, setFbData] = useState([]);

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
      setFbData(response.data.fb_data);
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

  return (
    <div className="form-container">

      <header className="header">AutoCompare</header>
      <p className="top-info">Simply enter the URL of an AutoTrader car that you like, and we will find you better deals. For free.</p>
      <form className="url-form" onSubmit={handleSubmit}>
        <input
          type="text"
          name="url"
          value={formData.url}
          onChange={handleChange}
          placeholder="Enter the car URL.."
        />
        <input
          type="text"
          name="location"
          value={formData.location}
          onChange={handleChange}
          placeholder="Enter your location (city)..."
          />
        <button type="submit" disabled={isLoading}>Submit</button>
      </form>

      {isLoading && (
        <div className="loading-text">
          <div className="lds-ring">
                    <div></div>
                    <div></div>
                    <div></div>
                    <div></div>
            </div>

            <p>Please wait while we fetch relevant deals!</p>
        </div>
      )}

      {data && (
        <div className="data-section">
          <h2>Your Chosen Car:</h2>
          <img src={data.image_url} className="scraped-car-img" alt="Car" />
          <div className="price-badge">
            <p className="price-text">Car Price: {data.price}</p>
          </div>
          <p>Car Brand: {data.brand}</p>
          <p>Car Model Type: {data.model_type}</p>
          <p>Car Registration: {data.registration}</p>
          <p>Car Mileage: {data.mileage} </p>
          <p>Previous Owners: {data.previous_owners}</p>
        </div>
      )}
    

        {isScrapeDone && (fbData && fbData.length > 0 ? (
          <div>
            <h2 className="header">Facebook Marketplace Deals:</h2>
            {fbData.map((item, index) => (
              <div className="fb-section" key={index}>
                
                <a href={item.link} target="_blank" rel="noopener noreferrer">
                  <img src={item.image} className="scraped-car-img" alt={`Facebook Deal ${index + 1}`} />
                </a>
                
                <div className="price-badge">
                  <p className="price-text">Price: {item.price}</p>
                </div>
                <p>Mileage: {item.mileage} mileage</p>
                <p>Model: {item.model}</p>
                <div className="deal-badge">
                  <p className='deal-text'>Deal: <a href={item.link} target="_blank" rel="noopener noreferrer">{item.link}</a></p>
                </div>
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
