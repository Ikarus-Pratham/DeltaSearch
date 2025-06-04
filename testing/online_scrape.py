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
from similarity import ImageSimilarityComparator

warnings.filterwarnings('ignore')

def extract_product_url(href, driver=None):
    """Enhanced product URL extraction with multiple strategies"""
    if not href or href == "No link found" or not href.strip():
        return "No link found"
    
    # print(f"Processing URL: {href}")
    
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
            # print(f"Found camera button with selector: {selector}")
            return element
        except:
            continue
    
    return None

def find_upload_elements(driver):
    """Try multiple strategies to find upload elements"""
    # print("Looking for upload interface...")
    time.sleep(3)
    
    upload_selectors = [
        "//div[contains(text(), 'Upload an image')]",
        "//div[contains(text(), 'Upload a file')]", 
        "//span[contains(text(), 'Upload')]",
        "//button[contains(text(), 'Upload')]",
        "//*[contains(@aria-label, 'Upload')]",
        "//div[@role='tab'][contains(text(), 'Upload')]",
        "//div[contains(@class, 'upload')]",
        "//*[contains(@data-tab, 'upload')]",
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
                        # print(f"Found upload element with selector: {selector}")
                        break
            if upload_element:
                break
        except:
            continue
    
    if upload_element:
        try:
            driver.execute_script("arguments[0].click();", upload_element)
            time.sleep(3)
            # print("Clicked upload tab")
        except Exception as e:
            # print(f"Failed to click upload tab: {e}")
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
            # print(f"Found file input with selector: {selector}")
            return file_input
        except:
            continue
    
    return None

def extract_exact_matches_results_targeted(driver):
    """Targeted extraction based on the actual HTML structure"""
    # print("Extracting results from Exact matches tab using targeted selectors...")
    results = []
    
    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.ULSxyf, div.MjjYud"))
        )
        # print("Results containers found!")
    except:
        pass
        # print("Timeout waiting for result containers")
    
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
                # print(f"Found {len(containers)} containers with selector: {selector}")
                result_containers = containers
                break
        except Exception as e:
            pass
            # print(f"Error with selector {selector}: {e}")
    
    if not result_containers:
        # print("No containers found with targeted selectors, falling back to broader search...")
        try:
            all_links = driver.find_elements(By.CSS_SELECTOR, "a.ngTNl.ggLgoc")
            result_containers = [link.find_element(By.XPATH, "./ancestor::div[contains(@class, 'ULSxyf') or contains(@class, 'MjjYud')]") for link in all_links[:10]]
            result_containers = [c for c in result_containers if c]
        except:
            # print("Fallback method also failed")
            return results
    
    # print(f"Processing {len(result_containers)} result containers...")
    
    for i, container in enumerate(result_containers[:20]):
        try:
            # print(f"\n--- Processing Container {i+1} ---")
            product_url = "No product link found"
            product_title = "No title found"
            
            try:
                link_element = container.find_element(By.CSS_SELECTOR, "a.ngTNl.ggLgoc")
                href = link_element.get_attribute("href")
                if href and not href.startswith(("javascript:", "#", "data:")):
                    product_url = extract_product_url(href, driver)
                    # print(f"Raw product URL: {href}")
                    # print(f"Processed product URL: {product_url}")
                else:
                    pass
                    # print("No valid href found in link element")
            except Exception as e:
                pass
                # print(f"Error extracting product URL: {e}")
            
            try:
                title_element = container.find_element(By.CSS_SELECTOR, "div.ZhosBf.T7iOye.MBI8Pd.dctkEf")
                product_title = title_element.text.strip()
                if product_title:
                    pass
                    # print(f"Title: {product_title}")
                else:
                    pass
                    # print("Title element found but text is empty")
            except Exception as e:
                # print(f"Error extracting title: {e}")
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
                # print(f"Image URL: {image_url[:100]}..." if len(str(image_url)) > 100 else f"Image URL: {image_url}")
            except Exception as e:
                pass
                # print(f"Error extracting image: {e}")
            
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
                    # print(f"Size: {size_text}")
            except:
                pass
            
            try:
                source_element = container.find_element(By.CSS_SELECTOR, "div.xuPcX.yUTMj.OSrXXb.m46kvb.PCBdKc")
                source_name = source_element.text.strip()
                if source_name:
                    metadata['source_name'] = source_name
                    source = source_name
                    # print(f"Source name: {source_name}")
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
                # print(f"✅ Result added: {len(results)} total results")
            else:
                pass
                # print("❌ Skipped result - no meaningful data extracted")
            
        except Exception as e:
            # print(f"❌ Error processing container {i+1}: {e}")
            continue
    
    return results

def download_image(url, save_path, index):
    """Download an image from a URL and save it to the specified path"""
    try:
        if not url.startswith("http"):
            # print(f"Skipping invalid URL: {url}")
            return False
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            with open(save_path, 'wb') as f:
                f.write(response.content)
            # print(f"Saved image: {save_path}")
            return True
        else:
            # print(f"Failed to download image {url}: Status code {response.status_code}")
            return False
    except Exception as e:
        # print(f"Error downloading image {url}: {e}")
        return False

def scrape_product_images(driver, product_url, save_folder="test", image_path=None):
    """Scrape all images from a product page within div.imgTagWrapper, including hidden ones, and save them to a folder"""
    # print(f"Navigating to product page: {product_url}")
    try:
        SimilarityComparator : ImageSimilarityComparator = ImageSimilarityComparator()
        driver.get(product_url)
        time.sleep(5)  # Wait for page to load
        
        # Create save folder if it doesn't exist
        if not os.path.exists(save_folder):
            os.makedirs(save_folder)
            # print(f"Created folder: {save_folder}")
        
        # Parse page source with BeautifulSoup to extract img tags within div.imgTagWrapper
        image_urls = set()  # Use set to avoid duplicates
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        img_tags = soup.find_all('img')
        
        # print(f"Found {len(img_tags)} div.imgTagWrapper elements in page source")
        
        for img in img_tags:
            src = img.get('src')
            data_src = img.get('data-src')
            zoom_src = img.get('data-zoom-image')
            
            # Prioritize zoomable or high-res images
            if zoom_src and "http" in zoom_src:
                image_urls.add(zoom_src)
            elif src and "http" in src and not src.startswith("data:"):
                image_urls.add(src)
            elif data_src and "http" in data_src and not data_src.startswith("data:"):
                image_urls.add(data_src)
        
        # Simulate hover on small images to trigger loading of hidden images
        try:
            thumbnail_selectors = [
                "div.imgTagWrapper img",  # Thumbnails within imgTagWrapper
                "img.thumbnail",  # Common thumbnail class
                "div.product-thumbnails img",  # Common thumbnail container
                "div.gallery img",  # Gallery-style thumbnails
                "img[src*='thumb']",  # Images with 'thumb' in URL
                "img"  # Fallback to any image
            ]
            
            for selector in thumbnail_selectors:
                try:
                    thumbnails = driver.find_elements(By.CSS_SELECTOR, selector)
                    # print(f"Found {len(thumbnails)} potential thumbnails with selector: {selector}")
                    for thumb in thumbnails:
                        try:
                            ActionChains(driver).move_to_element(thumb).perform()
                            time.sleep(0.5)  # Brief pause to allow dynamic content to load
                        except Exception as e:
                            # print(f"Error hovering over thumbnail: {e}")
                            continue
                except:
                    continue
            
            # Re-parse page source after hover actions
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            img_tags = soup.find_all('img')

            # print(f"Found {len(img_tags)} div.imgTagWrapper elements after hover actions")
            
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
        
        except Exception as e:
            pass
            # print(f"Error during hover simulation: {e}")
        
        # Fallback selectors for additional images
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
            except Exception as e:
                # print(f"Error with fallback selector {selector}: {e}")
                continue
        
        # print(f"Found {len(image_urls)} unique image URLs on product page")
        
        # Download each image
        for i, url in enumerate(image_urls, 1):
            flag = True
            file_extension = url.split('.')[-1].split('?')[0]
            if file_extension.lower() not in ['jpg', 'jpeg', 'png', 'webp']:
                flag = False
            if flag:
                save_path = os.path.join(save_folder, f"product_image_{i}.{file_extension}")
                download_image(url, save_path, i)
                score : int = SimilarityComparator.compare_images(image_path, save_path)
                if not score >= 0.85:
                    # print(f"Image {i} does not match original image closely enough, skipping. ", score)
                    os.remove(save_path)

        return list(image_urls)
    
    except Exception as e:
        # print(f"Error scraping product page: {e}")
        return []

def reverse_image_search_and_scrape(image_path, save_folder="test"):
    """Perform reverse image search, select first valid product, and scrape its images"""
    # Set up Chrome options
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    driver = None
    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        # Step 1: Perform reverse image search
        # print("Navigating to Google Images...")
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
                    # print("Cookie consent handled.")
                    break
                except:
                    continue
        except:
            pass
            # print("No cookie consent pop-up found.")
        
        # Find and click camera button
        # print("Searching for camera button...")
        camera_button = find_camera_button(driver)
        if not camera_button:
            raise Exception("Could not find camera button")
        
        # print("Camera button found, clicking...")
        driver.execute_script("arguments[0].click();", camera_button)
        time.sleep(3)
        
        # Find upload elements
        file_input = find_upload_elements(driver)
        if not file_input:
            raise Exception("Could not find file input element")
        
        # Upload the image file
        # print("Uploading image...")
        absolute_path = os.path.abspath(image_path)
        # print(f"Uploading file: {absolute_path}")
        file_input.send_keys(absolute_path)
        # print("Waiting for upload and processing...")
        time.sleep(10)
        
        # Look for exact matches tab
        # print("\n=== LOOKING FOR EXACT MATCHES TAB ===")
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
                            # print(f"Found Exact matches tab with selector: {selector}")
                            break
                if exact_matches_tab:
                    break
            except:
                continue
        
        if exact_matches_tab:
            # print("Clicking Exact matches tab...")
            driver.execute_script("arguments[0].click();", exact_matches_tab)
            time.sleep(5)
        
        # Step 2: Extract results and select first valid product
        results = extract_exact_matches_results_targeted(driver)
        # print(f"\n🎉 Successfully extracted {len(results)} results!")
        
        # Filter for valid product URLs
        valid_results = [r for r in results if r['product_url'] not in 
                        ["No link found", "No product URL found (Google search link)", 
                         "No product URL found in redirect", "No product URL found", 
                         "No product link found"] and r['product_url'].startswith('http')]
        
        if not valid_results:
            # print("No valid product URLs found in exact matches.")
            return {"error": "No valid product URLs found"}
        
        first_product = valid_results[0]
        # print(f"\nSelected first product: {first_product['title']}")
        # print(f"Product URL: {first_product['product_url']}")
        
        # Step 3: Scrape images from the product page
        image_urls = scrape_product_images(driver, first_product['product_url'], save_folder, image_path)
        
        return {
            "product_title": first_product['title'],
            "product_url": first_product['product_url'],
            "source": first_product['source'],
            "image_urls": image_urls,
            "metadata": first_product['metadata']
        }
        
    except Exception as e:
        # print(f"❌ An error occurred: {str(e)}")
        return {"error": str(e)}
        
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass

if __name__ == "__main__":
    try:
        image_path = "liten.webp"  # Change this to your image path
        save_folder = "test"  # Folder to save images
        # print(f"Starting enhanced reverse image search and scrape for: {image_path}")
        result = reverse_image_search_and_scrape(image_path, save_folder)
        
        if "error" in result:
            pass
            # print(f"Error: {result['error']}")
        else:
            # print(f"\n🎉 Successfully processed product!")
            # print(f"Product Title: {result['product_title']}")
            # print(f"Product URL: {result['product_url']}")
            # print(f"Source: {result['source']}")
            # print(f"Found and saved {len(result['image_urls'])} images to '{save_folder}' folder")
            # print("Image URLs:")
            for i, url in enumerate(result['image_urls'], 1):
                pass
                # print(f"{i}. {url}")
            if result.get('metadata'):
                pass
                # print(f"Metadata: {result['metadata']}")
            
    except Exception as e:
        pass
        # print(f"❌ Failed to execute: {str(e)}")