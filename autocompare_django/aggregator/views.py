from django.shortcuts import render, redirect
from .forms import CarURLForm
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from selenium import webdriver
from selenium.webdriver import Chrome
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC

# Create your views here.

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

            driver.quit()

            motors_data = search_motors_similar(data)

            response_data = {
                'data': data,
                'motors_data': motors_data,
            }
            return Response(response_data, status=200)
        else:
            return Response({"error": "Invalid form"}, status=400)
        
    return Response({"error": "Method not allowed"}, status=405)


def search_motors_similar(data):
    trusted_domain = "motors.co.uk"
    query = f"{data['brand']} {data['registration']} with {data['mileage']} for sale Motors UK"

    driver = Chrome()
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

                scraped_data = {
                'price': price,
                'link': link,
                'mileage': mileage
                }
                scraped_data_list.append(scraped_data)

        except Exception as e:
            print(f"Error while scraping price: {e}")
            scraped_data = {
                'price': 'Error',
                'link': 'Error'
            }

    driver.quit()

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