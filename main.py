import eel
import os
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import undetected_chromedriver as webdriver
from selenium.webdriver.common.action_chains import ActionChains
from urllib.parse import urlparse, parse_qs, unquote
import time
import warnings
from bs4 import BeautifulSoup
from similarity import ImageSimilarityComparator  # Ensure this is available
import base64
import io
from PIL import Image

warnings.filterwarnings('ignore')

# Initialize Eel
eel.init('web')

def extract_product_url(href, driver=None):
    """Enhanced product URL extraction with multiple strategies"""
    if not href or href == "No link found" or not href.strip():
        return "No link found"
    
    if href.startswith(("javascript:", "#", "data:")):
        return "No product URL found"
    
    parsed_url = urlparse(href)
    
    if parsed_url.netloc in ("www.google.com", "google.com") and parsed_url.path.startswith("/url"):
        query_params = parse_qs(parsed_url.query)
        actual_url = query_params.get("url", [None])[0] or query_params.get("q", [None])[0]
        if actual_url and actual_url.startswith("http"):
            return unquote(actual_url)
        return "No product URL found in redirect"
    
    if parsed_url.netloc in ("www.google.com", "google.com") and parsed_url.path.startswith("/search"):
        return "No product URL found (Google search link)"
    
    if "shopping" in href or "product" in href or "merchant" in href:
        query_params = parse_qs(parsed_url.query)
        merchant_url = query_params.get("merchant_url", [None])[0] or query_params.get("pdp_url", [None])[0]
        if merchant_url:
            return unquote(merchant_url)
    
    if href.lower().endswith('.pdf'):
        return f"PDF catalog link: {href}"
    
    try:
        response = requests.head(href, allow_redirects=True, timeout=5)
        final_url = response.url
        if "google.com" not in final_url:
            return final_url
    except:
        pass
    
    if "google.com" not in parsed_url.netloc:
        return href
    
    return "No product URL found"

def find_camera_button(driver):
    """Try multiple strategies to find the camera button"""
    selectors = [
        "//button[@aria-label='Search by image']",
        "//div[@aria-label='Search by image']",
        "//button[contains(@class, 'Gdd5U')]",
        "//div[contains(@class, 'nDcEnd')]",
        "//button[@data-ved]",
        "//*[contains(@aria-label, 'camera')]",
        "//*[contains(@title, 'camera')]",
        "//*[contains(@aria-label, 'image')]",
        "//*[contains(@class, 'camera')]",
        "//div[@role='button'][contains(@aria-label, 'Search')]",
        "//span[contains(@class, 'z1asCe')]//parent::div[@role='button']",
        "//div[@jsname='RNNXgb']",
        "//div[contains(@class, 'HDL7pd')]//parent::div[@role='button']"
    ]
    
    for selector in selectors:
        try:
            element = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, selector))
            )
            return element
        except:
            continue
    
    return None

def find_upload_elements(driver):
    """Try multiple strategies to find upload elements"""
    time.sleep(3)
    
    upload_selectors = [
        "//div[contains(text(), 'Upload an image')]",
        "//div[contains(text(), 'Upload a file')]", 
        "//span[contains(text(), 'Upload')]",
        "//button[contains(text(), 'Upload')]",
        "//*[contains(@aria-label, 'Upload')]",
        "//div[@role='tab'][contains(text(), 'Upload')]",
        "//div[contains(@class, 'upload')]",
        "//*[@data-tab='upload']",
        "//div[contains(@class, 'Gdd5U')][@role='tab']",
        "//div[@role='tab']"
    ]
    
    upload_element = None
    for selector in upload_selectors:
        try:
            elements = driver.find_elements(By.XPATH, selector)
            for element in elements:
                if element.is_displayed() and element.is_enabled():
                    text = element.text.lower()
                    if 'upload' in text:
                        upload_element = element
                        break
            if upload_element:
                break
        except:
            continue
    
    if upload_element:
        try:
            driver.execute_script("arguments[0].click();", upload_element)
            time.sleep(3)
        except:
            pass
    
    file_input_selectors = [
        "//input[@type='file']",
        "//input[@accept*='image']",
        "//*[@type='file']"
    ]
    
    for selector in file_input_selectors:
        try:
            file_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, selector))
            )
            return file_input
        except:
            continue
    
    return None

def extract_exact_matches_results_targeted(driver):
    """Targeted extraction based on the actual HTML structure"""
    results = []
    
    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.ULSxyf, div.MjjYud"))
        )
    except:
        pass
    
    container_selectors = [
        "div.ULSxyf",
        "div.MjjYud",
        "div.ULSxyf div.MjjYud"
    ]
    
    result_containers = []
    for selector in container_selectors:
        try:
            containers = driver.find_elements(By.CSS_SELECTOR, selector)
            if containers:
                result_containers = containers
                break
        except:
            pass
    
    if not result_containers:
        try:
            all_links = driver.find_elements(By.CSS_SELECTOR, "a.ngTNl.ggLgoc")
            result_containers = [link.find_element(By.XPATH, "./ancestor::div[contains(@class, 'ULSxyf') or contains(@class, 'MjjYud')]") for link in all_links[:10]]
            result_containers = [c for c in result_containers if c]
        except:
            return results
    
    for i, container in enumerate(result_containers[:20]):
        try:
            product_url = "No product link found"
            product_title = "No title found"
            
            try:
                link_element = container.find_element(By.CSS_SELECTOR, "a.ngTNl.ggLgoc")
                href = link_element.get_attribute("href")
                if href and not href.startswith(("javascript:", "#", "data:")):
                    product_url = extract_product_url(href, driver)
            except:
                pass
            
            try:
                title_element = container.find_element(By.CSS_SELECTOR, "div.ZhosBf.T7iOye.MBI8Pd.dctkEf")
                product_title = title_element.text.strip()
                if not product_title:
                    fallback_selectors = ["h3", "div[role='heading']", ".wyccme div"]
                    for fallback_selector in fallback_selectors:
                        try:
                            fallback_title = container.find_element(By.CSS_SELECTOR, fallback_selector)
                            text = fallback_title.text.strip()
                            if text and len(text) > 3:
                                product_title = text
                                break
                        except:
                            continue
            except:
                pass
            
            image_url = "No image found"
            try:
                img_selectors = [
                    "div.zVq10e.uhHOwf.ez24Df img",
                    "img[id^='dimg_']",
                    "div.GmoL0c img",
                    "img[src*='http']",
                    "img"
                ]
                for img_selector in img_selectors:
                    try:
                        img_elements = container.find_elements(By.CSS_SELECTOR, img_selector)
                        for img in img_elements:
                            src = img.get_attribute("src")
                            data_src = img.get_attribute("data-src")
                            if src and not src.startswith("data:") and "http" in src:
                                image_url = src
                                break
                            elif data_src and not data_src.startswith("data:") and "http" in data_src:
                                image_url = data_src
                                break
                            elif src and len(src) > 50:
                                image_url = src[:100] + "..." if len(src) > 100 else src
                                break
                        if image_url != "No image found":
                            break
                    except:
                        continue
            except:
                pass
            
            source = "Unknown source"
            if product_url and product_url.startswith("http"):
                try:
                    parsed = urlparse(product_url)
                    source = parsed.netloc.replace("www.", "")
                except:
                    pass
            
            metadata = {}
            try:
                size_element = container.find_element(By.CSS_SELECTOR, "span.cyspcb.DH9lqb.VBZLA span")
                size_text = size_element.text.strip()
                if size_text and 'x' in size_text:
                    metadata['size'] = size_text
            except:
                pass
            
            try:
                source_element = container.find_element(By.CSS_SELECTOR, "div.xuPcX.yUTMj.OSrXXb.m46kvb.PCBdKc")
                source_name = source_element.text.strip()
                if source_name:
                    metadata['source_name'] = source_name
                    source = source_name
            except:
                pass
            
            if (product_url not in ["No product link found", "No product URL found"] or 
                product_title not in ["No title found"] or 
                image_url not in ["No image found"]):
                result = {
                    "title": product_title,
                    "image_url": image_url,
                    "product_url": product_url,
                    "source": source,
                    "metadata": metadata
                }
                results.append(result)
            
        except:
            continue
    
    return results

def download_image(url, save_path, index):
    """Download an image from a URL and save it to the specified path"""
    try:
        if not url.startswith("http"):
            return False
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            with open(save_path, 'wb') as f:
                f.write(response.content)
            return True
        return False
    except:
        return False

def scrape_product_images(driver, product_url, save_folder, image_path):
    """Scrape all images from a product page within div.imgTagWrapper"""
    try:
        SimilarityComparator = ImageSimilarityComparator()
        driver.get(product_url)
        time.sleep(5)
        
        if not os.path.exists(save_folder):
            os.makedirs(save_folder)
        
        image_urls = set()
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        img_tags = soup.find_all('img')
        
        for img in img_tags:
            src = img.get('src')
            data_src = img.get('data-src')
            zoom_src = img.get('data-zoom-image')
            
            if zoom_src and "http" in zoom_src:
                image_urls.add(zoom_src)
            elif src and "http" in src and not src.startswith("data:"):
                image_urls.add(src)
            elif data_src and "http" in data_src and not data_src.startswith("data:"):
                image_urls.add(data_src)
        
        try:
            thumbnail_selectors = [
                "div.imgTagWrapper img",
                "img.thumbnail",
                "div.product-thumbnails img",
                "div.gallery img",
                "img[src*='thumb']",
                "img"
            ]
            
            for selector in thumbnail_selectors:
                try:
                    thumbnails = driver.find_elements(By.CSS_SELECTOR, selector)
                    for thumb in thumbnails:
                        try:
                            ActionChains(driver).move_to_element(thumb).perform()
                            time.sleep(0.5)
                        except:
                            continue
                except:
                    continue
            
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            img_tags = soup.find_all('img')
            
            for img in img_tags:
                src = img.get('src')
                data_src = img.get('data-src')
                zoom_src = img.get('data-zoom-image')
                
                if zoom_src and "http" in zoom_src:
                    image_urls.add(zoom_src)
                elif src and "http" in src and not src.startswith("data:"):
                    image_urls.add(src)
                elif data_src and "http" in data_src and not data_src.startswith("data:"):
                    image_urls.add(data_src)
        
        except:
            pass
        
        fallback_selectors = [
            "img[src*='product']",
            "img[alt*='product']",
            "img[data-zoom-image]",
            "img[src*='image']",
            "div.product-image img",
            "div.gallery img",
            "img[src*='http']",
            "img"
        ]
        
        for selector in fallback_selectors:
            try:
                images = driver.find_elements(By.CSS_SELECTOR, selector)
                for img in images:
                    src = img.get_attribute("src")
                    data_src = img.get_attribute("data-src")
                    zoom_src = img.get_attribute("data-zoom-image")
                    
                    if zoom_src and "http" in zoom_src:
                        image_urls.add(zoom_src)
                    elif src and "http" in src and not src.startswith("data:"):
                        image_urls.add(src)
                    elif data_src and "http" in data_src and not data_src.startswith("data:"):
                        image_urls.add(data_src)
            except:
                continue
        
        for i, url in enumerate(image_urls, 1):
            flag = True
            file_extension = url.split('.')[-1].split('?')[0]
            if file_extension.lower() not in ['jpg', 'jpeg', 'png', 'webp']:
                flag = False
            if flag:
                save_path = os.path.join(save_folder, f"product_image_{i}.{file_extension}")
                if download_image(url, save_path, i):
                    score = SimilarityComparator.compare_images(image_path, save_path)
                    if not score >= 0.85:
                        os.remove(save_path)
        
        return list(image_urls)
    
    except:
        return []

@eel.expose
def reverse_image_search_and_scrape(image_data, save_folder="test"):
    """Perform reverse image search and scrape images, adapted for Eel"""
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    driver = None
    try:
        if not os.path.exists(save_folder):
            os.makedirs(save_folder)
        
        # clear any existing images in the save folder
        for file in os.listdir(save_folder):
            file_path = os.path.join(save_folder, file)
            if os.path.isfile(file_path):
                os.remove(file_path)

        # Save base64 image to temporary file
        image_data = image_data.split(',')[1]  # Remove data:image/jpeg;base64, prefix
        image_bytes = base64.b64decode(image_data)
        temp_image_path = os.path.join(save_folder, "temp_image.jpg")
        with open(temp_image_path, 'wb') as f:
            f.write(image_bytes)
        
        driver = webdriver.Chrome(options=chrome_options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        driver.get("https://images.google.com")
        time.sleep(5)
        
        # Handle cookie consent
        try:
            accept_selectors = [
                "//button[contains(text(), 'Accept')]",
                "//button[contains(text(), 'I agree')]", 
                "//button[contains(text(), 'Accept all')]",
                "//div[contains(text(), 'Accept')][@role='button']",
                "//button[@id='L2AGLb']"
            ]
            for selector in accept_selectors:
                try:
                    accept_button = WebDriverWait(driver, 3).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    accept_button.click()
                    time.sleep(2)
                    break
                except:
                    continue
        except:
            pass
        
        camera_button = find_camera_button(driver)
        if not camera_button:
            raise Exception("Could not find camera button")
        
        driver.execute_script("arguments[0].click();", camera_button)
        time.sleep(3)
        
        file_input = find_upload_elements(driver)
        if not file_input:
            raise Exception("Could not find file input element")
        
        file_input.send_keys(os.path.abspath(temp_image_path))
        time.sleep(10)
        
        exact_matches_selectors = [
            "//div[@role='tab'][contains(text(), 'Exact matches')]",
            "//div[contains(text(), 'Exact matches')][@role='tab']",
            "//span[contains(text(), 'Exact matches')]",
            "//div[contains(@class, 'tab')][contains(text(), 'Exact matches')]",
            "//*[contains(text(), 'Exact matches')]"
        ]
        
        exact_matches_tab = None
        for selector in exact_matches_selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                for element in elements:
                    if element.is_displayed() and element.is_enabled():
                        text = element.text.lower()
                        if 'exact' in text and 'match' in text:
                            exact_matches_tab = element
                            break
                if exact_matches_tab:
                    break
            except:
                continue
        
        if exact_matches_tab:
            driver.execute_script("arguments[0].click();", exact_matches_tab)
            time.sleep(5)
        
        results = extract_exact_matches_results_targeted(driver)
        
        valid_results = [r for r in results if r['product_url'] not in 
                        ["No link found", "No product URL found (Google search link)", 
                         "No product URL found in redirect", "No product URL found", 
                         "No product link found"] and r['product_url'].startswith('http')]
        
        if not valid_results:
            return {"error": "No valid product URLs found"}
        
        first_product = valid_results[0]
        image_urls = scrape_product_images(driver, first_product['product_url'], save_folder, temp_image_path)
        
        # Convert saved images to base64 for frontend display
        saved_images = []
        for img_file in os.listdir(save_folder):
            if img_file.startswith("product_image_"):
                img_path = os.path.join(save_folder, img_file)
                with open(img_path, 'rb') as f:
                    img_data = base64.b64encode(f.read()).decode('utf-8')
                    saved_images.append(f"data:image/{img_file.split('.')[-1]};base64,{img_data}")
        
        return {
            "product_title": first_product['title'],
            "product_url": first_product['product_url'],
            "source": first_product['source'],
            "image_urls": image_urls,
            "saved_images": saved_images,
            "metadata": first_product['metadata']
        }
        
    except Exception as e:
        return {"error": str(e)}
        
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass
        # Clean up temporary image
        if os.path.exists(temp_image_path):
            os.remove(temp_image_path)

# Start Eel
if __name__ == "__main__":
    eel.start('index.html', size=(800, 600))
    