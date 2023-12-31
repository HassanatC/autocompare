from django.shortcuts import render, redirect
from .forms import CarURLForm
from django.core.cache import cache
from django.http import JsonResponse
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from selenium import webdriver
from selenium.webdriver import Chrome
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from urllib.parse import urljoin
import re
import time
import json

# Create your views here.

@api_view(['POST'])
def main_view(request):
    if request.method == 'POST':
        form = CarURLForm(request.data)
        if form.is_valid():
            url = form.cleaned_data['url']
            location = form.cleaned_data['location']
            driver = Chrome()

            data = scrape_car_data(url, driver)
            fb_data = search_fb(data, driver, location)
            driver.quit()

            if not fb_data:
                return Response({"error": "FB Marketplace data could not be scraped"}, status=500)

            return Response({"data": data,
                              "fb_data": fb_data}, status=200)
        else:
            return Response({"error": "Invalid form"}, status=400)
    else:
        return Response({"error": "Method not allowed"}, status=405)

def scrape_car_data(url, driver):
    data = {}
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
        model_type_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'span[data-testid="advert-subtitle"]')))
        data["model_type"] = model_type_element.text
    except Exception as e:
        data["model_type"] = f"Error: {e}"

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

    return data

def search_fb(data, driver, location):
    trusted_domain = "facebook.com/marketplace"
    query = f"facebook marketplace {location} used {data['brand']} {data['registration']} {data['mileage']} for sale"
    fallback_text = "for sale in"

    driver.get("https://www.google.com")

    handle_cookie_popup(driver)

    search_box = driver.find_element(By.NAME, "q")
    search_box.send_keys(query)
    search_box.submit()

    wait = WebDriverWait(driver, 10)
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "h3")))

    scraped_data_list = []

    #search for relevant link, use xpath and query to find and crawl. loop and conditions to find a link that isn't login blocked
    search_results = driver.find_elements(By.XPATH, "//h3/ancestor::a")
    correct_link = None
    fallback_link = None

    first_brand_keyword = data['brand'].split()[0]
    
    for link_element in search_results:
        link_url = link_element.get_attribute("href") or ""
        try:
            h3_element = link_element.find_element(By.XPATH, "./h3")
            link_text = h3_element.text if h3_element else ""
        except NoSuchElementException:
            print(f"No h3 element found for {link_url}")
            continue

        if trusted_domain in link_url:
            if "New and used" in link_text:
                continue
            if first_brand_keyword in link_text.split():
                correct_link = link_url
                break
            elif fallback_text in link_text and fallback_link is None:
                fallback_link = link_url

    final_link = correct_link or fallback_link

    if final_link:
        driver.get(final_link)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.x78zum5')))

        # accurately scrapes price by locating parent and child elements in loop
        parent_elements = driver.find_elements(By.XPATH, "//div[@class='x9f619 x78zum5 x1r8uery xdt5ytf x1iyjqo2 xs83m0k x1e558r4 x150jy0e x1iorvi4 xjkvuk6 xnpuxes x291uyu x1uepa24']")

        for parent in parent_elements:
            try:
                price_element = parent.find_element(By.XPATH, ".//span[@dir='auto' and contains(@class, 'x193iq5w')]")
                price_text = price_element.text.replace('£', '').replace(',', '')
                #skip if price is non numeric i.e 'free'
                try:
                    float(price_text)
                except ValueError:
                    continue

                model_element = parent.find_element(By.XPATH, ".//span[@class='x1lliihq x6ikm8r x10wlt62 x1n2onr6']")
                mileage_element = parent.find_element(By.XPATH, ".//span[contains(@class, 'xlyipyv xuxw1ft x1j85h84') and contains(text(), 'km')]")
                link_element = parent.find_element(By.XPATH, ".//a[contains(@class, 'x1i10hfl')]")
                image_element = parent.find_element(By.XPATH, ".//img[@class='xt7dq6l xl1xv1r x6ikm8r x10wlt62 xh8yej3']")

                relative_link = link_element.get_attribute("href")
                absolute_link = urljoin("https://www.facebook.com", relative_link)
                mileage_text = mileage_element.text if 'km' in mileage_element.text else 'N/A'
                image_url = image_element.get_attribute('src')

                scraped_data_list.append({
                "price": price_element.text,
                "model": model_element.text.title(),
                "mileage": mileage_text,
                "link": absolute_link,
                "image": image_url
            })
            except NoSuchElementException:
                continue
        return scraped_data_list

def merge_data_lists(existing_data_list, scraped_data_list):
    return existing_data_list + scraped_data_list

def sort_scraped_data_by_price(fb_data):
    #sort the lists and return
    for item in fb_data:
        if 'price' in item:
            try:
                item['price'] = float(item['price'].replace('£', '').replace(',', ''))
            except ValueError:
                item['price'] = float('inf')
    
    sorted_fb_data = sorted(fb_data, key=lambda x: x.get('price', float('inf')))
    return sorted_fb_data[:12]

def handle_cookie_popup(driver):
    try:
        accept_button = WebDriverWait(driver, 1).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "div[role='none'][class='QS5gu sy4vM']"))
        )
        accept_button.click()
    except Exception as e:
        print(f"Error handling cookie popup: {e}")