from django.shortcuts import render, redirect
from .forms import CarURLForm
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from selenium import webdriver
from selenium.webdriver import Chrome
import re
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC

# Create your views here.

logging.basicConfig(level=logging.INFO)

@api_view(['POST'])
def scrape_car_data(request):

    data = {}
    motors_data = {}
    form = CarURLForm()

    if request.method == 'POST':
        form = CarURLForm(request.data)
        if form.is_valid():
            url = form.cleaned_data['url']

            driver = Chrome()
            driver.get(url)
            wait = WebDriverWait(driver, 1)

            try:
                price_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'h2[data-testid="advert-price"]')))
                data["price"] = price_element.text
            except Exception as e:
                data["price"] = f"Error: {e}"

            try:
                image_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'img')))
                data["image_url"] = image_element.get_attribute('src')
            except Exception as e:
                data["image_url"] = f"Error: {e}"
            try:
                brand_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'p[data-testid="advert-title"]')))
                data["brand"] = brand_element.text
            except Exception as e:
                data["brand"] = f"Error: {e}"

            try:
                mileage_element = wait.until(EC.presence_of_element_located((By.XPATH, "//div[contains(text(), 'Mileage')]/following-sibling::p")))
                data["mileage"] = mileage_element.text
            except Exception as e:
                data["mileage"] = f"Error: {e}"

            try:
                registration_element = wait.until(EC.presence_of_element_located((By.XPATH, "//div[contains(text(), 'Registration')]/following-sibling::p")))
                data["registration"] = registration_element.text
            except Exception as e:
                data["registration"] = f"Error: {e}"

            try:
                previous_owners_element = wait.until(EC.presence_of_element_located((By.XPATH, "//div[contains(text(), 'Previous')]/following-sibling::p")))
                full_text = previous_owners_element.text
                owner_count_match = re.search(r'\d+', full_text)
                if owner_count_match:
                    owner_count = owner_count_match.group() 
                    data["previous_owners"] = owner_count
                else:
                    data["previous_owners"] = "Could not determine"
            except Exception as e:
                data["previous_owners"] = f"Not Available"


            motors_data = search_motors_similar(data, driver)

            response_data = {
                'data': data,
                'motors_data': motors_data,
            }
            return Response(response_data, status=200)
        else:
            return Response({"error": "Invalid form"}, status=400)
        
    return Response({"error": "Method not allowed"}, status=405)


def main(data):
    try:
        driver = Chrome()
        motors_data = search_motors_similar(data, driver)
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        driver.quit()

    return motors_data

def search_motors_similar(data, driver):
    trusted_domain = "motors.co.uk"
    query = f"{data['brand']} {data['registration']} with {data['mileage']} for sale Motors UK"

    driver.get("https://www.google.com")

    handle_cookie_popup(driver)

    search_box = driver.find_element(By.NAME, "q")
    search_box.send_keys(query)
    search_box.submit()

    wait = WebDriverWait(driver, 1)
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "h3")))
    
    #finds the relevant motors link
    search_results = driver.find_elements(By.XPATH, "//h3/ancestor::a")
    all_links = [link.get_attribute("href") for link in search_results if link.get_attribute("href")]

    motors_links = [link for link in all_links if link and trusted_domain in link]

    scraped_data = {}
    #if motors link is found, proceed to scrap the price. rudimentary currently
    
    if motors_links:
        motors_link_to_click = motors_links[0]
        link_element = driver.find_element(By.XPATH, f"//a[@href='{motors_link_to_click}']")
        wait.until(EC.element_to_be_clickable((By.XPATH, f"//a[@href='{motors_link_to_click}']")))
        link_element.click()
    
        try:
            wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".title-3")))
      
            print("Trying to find price elements...")
            price_elements = driver.find_elements(By.CSS_SELECTOR, ".title-3")
            scraped_data_list = []

            # loops through the price elements in motors. finds them and scrapes
            for price_element in price_elements:
                parent_element = price_element.find_element(By.XPATH, "./ancestor::div[contains(@class, 'result-card box-shadow-hover')]")

                price = price_element.text
                print(f"Price element found. Text: {price}")

                link_element = parent_element.find_element(By.CSS_SELECTOR, "a.result-card__link")
                link = link_element.get_attribute("href")

                mileage_element = parent_element.find_element(By.CSS_SELECTOR, "span.vehicle-info__mileage")
                mileage = mileage_element.text
                print(f"Mileage element found. Text: {mileage}")

                image_element = parent_element.find_element(By.CSS_SELECTOR, ".result-card__image-container .lazy img")
                thumbnail_image = image_element.get_attribute('src')

                scraped_data = {
                'price': price,
                'link': link,
                'mileage': mileage,
                'thumbnail_image': thumbnail_image
                }
                scraped_data_list.append(scraped_data)

        except Exception as e:
            print(f"Error while scraping price: {e}")
            scraped_data = {
                'price': 'Error',
                'link': 'Error'
            }

    print("Motors Link:", motors_links)
    print("Scraped Data:", scraped_data_list)

    scraped_data_list = sort_scraped_data_by_price(scraped_data_list)
    return scraped_data_list

def sort_scraped_data_by_price(scraped_data_list):
    #method to sort the returned data by cheapest first. currently the standard
    scraped_data_list = [
        {k: float(v.replace('£', '').replace(',', '')) if k == 'price' else v for k, v in item.items()}
        for item in scraped_data_list
    ]

    #sort the list of dictionaries
    sorted_list = sorted(scraped_data_list, key=lambda x: x['price'])
    return sorted_list[:10]

def handle_cookie_popup(driver):
    try:
        accept_button = WebDriverWait(driver, 1).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "div[role='none'][class='QS5gu sy4vM']"))
        )
        accept_button.click()
    except Exception as e:
        print(f"Error handling cookie popup: {e}")


# will work on soon
"""
def search_facebook(data, driver):

    trusted_domain = "facebook.com/marketplace"
    query = f"{data['brand']} {data['registration']} {data['mileage']}facebook marketplace"

    driver.get("https://www.google.com")
    handle_cookie_popup(driver)

    search_box = driver.find_element(By.NAME, "q")
    search_box.send_keys(query)
    search_box.submit()

    wait = WebDriverWait(driver, 5)
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "h3")))

    search_results = driver.find_elements(By.XPATH, "//h3/ancestor::a")
    all_links = [link.get_attribute("href") for link in search_results if link.get_attribute("href")]

    fb_links = [link for link in all_links if link and trusted_domain in link]
    scraped_data_list = []

    if fb_links:
        fb_link_to_click = fb_links[0]
        link_element = driver.find_element(By.XPATH, f"//a[@href='{fb_link_to_click}']")
        wait.until(EC.element_to_be_clickable((By.XPATH, f"//a[@href='{fb_link_to_click}']")))
        link_element.click()
"""

"""
def login_facebook(driver):
    fb_email = 'haroldahmed431@gmail.com'
    fb_pass = 'Ajmerian55'

    try:
        logging.info("Attempting to handle cookie popup")
        handle_cookie_popup(driver)

        logging.info("Attempting to find email element.")
        email_elem = driver.find_element(By.ID, "email")
        email_elem.send_keys(fb_email)

        logging.info("attempting to find password element")
        pass_elem = driver.find_element(By.ID, "pass")
        pass_elem.send_keys(fb_pass)
        
        pass_elem.send_keys(Keys.RETURN)
    except Exception as e:
        logging.error(f"Error while logging into Facebook: {e}")
"""