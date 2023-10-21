from locust import HttpUser, task, between

import json

class UserBehavior(HttpUser):
    wait_time = between(1, 3)

    @task(1)
    def submit_form(self):
        autotrader_url = "https://www.autotrader.co.uk/car-details/202309302518068?sort=price-desc&advertising-location=at_cars&include-delivery-option=on&make=BMW&model=3%20Series&postcode=sl11nj&price-from=3500&price-to=9500&year-from=2012&fromsra" 
        location = "London"

        response = self.client.post("scrape/", {
            "url": autotrader_url,
            "location": location
        })

        if response.status_code == 200:
            returned_data = response.json()
            if "error" not in returned_data:
                try:
                    with open("C:/Users/hassa/Desktop/test_json/locust_responses.jsonl", "a") as f:
                        f.write(json.dumps(returned_data))
                        f.write("\n")
                except Exception as e:
                    print(f"An error occured: {e}")
        
            else:
                print(f"Error: {returned_data['error']}")

        if response.status_code != 200:
            print(f"Failed POST request. Status code: {response.status_code}")