from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
import time, json
import os
import time
import requests
import re



def get_meta(meta_content):
    '''
    Get Meta data from static webpage
    '''
    meta = str( meta_content.get('content') )
    meta = meta.replace('\xa0', '').replace(' ', '').replace('\n','')
    meta = meta.split('|')
    statistic, content, poster = meta[0], meta[1], meta[2]
    num_views, num_faces = statistic.replace(',','').split('·')[0], statistic.replace(',','').split('·')[1]
    num_view, num_face = num_views.split('次觀看')[0], re.search(r'\d+', num_faces).group(0)

    parts = content.partition('#')    
    video_content, reel_tag = [parts[0], parts[1] + parts[2]][0], [parts[0], parts[1] + parts[2]][1]

    return num_view, num_face, video_content, reel_tag, poster

def get_static_data(url):
    # Get static web content: 標記, 內文, 發文者, 表情數
    
    res = requests.get(url)
    soup = BeautifulSoup(res.text, 'html.parser')
    meta_content = soup.find('meta', property="og:title")

    num_view, num_face, video_content, reel_tag, poster = get_meta(meta_content)
    
    print("Number of views: ", num_view)
    print("Number of faces: ", num_face)
    print("Content of video: ", video_content)
    print("Reel video tag: ", reel_tag)
    print("Poster of the Video: ", poster)

    result = {"Reel 標記": reel_tag, "Reel 內文": video_content, "Reel 發文者": poster, "Reel 表情數": num_face}
    return result


def create_persistent_browser(profile_dir):
    # 避免 Facebook 重複登入需求
    options = webdriver.ChromeOptions()
    options.add_argument(f"--user-data-dir={profile_dir}")
    options.add_argument("--disable-notifications")
    
    service = Service(executable_path=r"C:\Users\User\laurence\drivers\chromedriver.exe")
    browser = webdriver.Chrome(service=service, options=options)
    return browser


def get_share_count_and_num_comments(browser):
    """
    取得 分享數量 和 評論數量
    """

    try:
        # 1. Share count
        # Find the parent div containing the aria-label="分享" button
        parent_div = WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[@aria-label='分享']/ancestor::div[1]"))
        )

        # Find the sibling div containing the share count
        sibling_div = parent_div.find_element(By.XPATH, "following-sibling::div[1]")

        # Find the span containing the share count
        share_count_span = sibling_div.find_element(By.XPATH, ".//span")
        print("Share count span: ", share_count_span)

        # Extract the text
        share_count = share_count_span.text.strip()
        print(f"Share count: {share_count}")

        # 2. Comment count
        parent_div = WebDriverWait(browser, 5).until(
            EC.presence_of_element_located((By.XPATH, "//div[@aria-label='留言']/ancestor::div[1]"))
        )
        # Find the sibling div containing the share count
        sibling_div = parent_div.find_element(By.XPATH, "following-sibling::div[1]")

        # Find the span containing the share count
        comment_count_span = sibling_div.find_element(By.XPATH, ".//span")
        print("Comment count span: ", comment_count_span)

        # Extract the text
        comment_count = comment_count_span.text.strip()
        print(f"Comment count: {comment_count}")

        return share_count, comment_count

    except TimeoutException:
        print("Share count element not found within the timeout.")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None


def click_require_button(browser):
    # Wait for comments to be visible - using more generic selectors
        print("Start to click comment button")
        comment_button = WebDriverWait(browser, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//div[@aria-label="留言" and @aria-expanded="false"]'))
        )
        comment_button.click()
        print("Start click Show all comments button: 最相關")
        # Click 'All comments'
        all_comment_button = WebDriverWait(browser, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//span[contains( text(),'最相關' )]"))
                )
        time.sleep(2)
        all_comment_button.click() # If the button is found, click it
        # Click 'Display all comments'
        print("Start click Show all comments button: 顯示所有留言")
        show_all_button = WebDriverWait(browser, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//span[contains( text(), '顯示所有留言，包含可能是垃圾訊息的內容' )]"))
                )
        time.sleep(2)
        show_all_button.click() # If the button is found, click it

def click_reply_buttons(browser):
    """Clicks all '查看 X 則回覆' buttons and '查看更多' on the page"""

    # Click 查看更多
    try:
        more_button = WebDriverWait(browser, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//div[text()='查看更多' and @role='button']"))
        )
        time.sleep(2)
                # If the button is found, click it
        more_button.click()
        print("Found and clicked '查看更多' button")
    except TimeoutException:
                # If the button isn't found within the timeout period, just continue
        print("No '查看更多' button found, continuing with the script")

    # Click 查看回復
    try:
        while True:
            # Find all reply buttons
            reply_buttons = WebDriverWait(browser, 10).until(
                EC.presence_of_all_elements_located((By.XPATH, "//span[contains(text(), '查看') and contains(text(), '則回覆')]"))
            )

            if not reply_buttons:
                print("No more '查看 X 則回覆' buttons found.")
                break  # Exit the loop if no buttons are found

            for button in reply_buttons:
                try:
                    # Use JavaScript to click, to avoid interception issues
                    browser.execute_script("arguments[0].click();", button)
                    print("Reply button clicked.")
                    time.sleep(2) #wait for comments to load.

                except Exception as e:
                    print(f"Error clicking reply button: {e}")

    except TimeoutException:
        print("Timeout waiting for reply buttons.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


def access_facebook_content(url, profile_dir):
    # Create browser with persistent profile
    browser = create_persistent_browser(profile_dir)

    static_content = get_static_data(url)

    try:
        comment_data = [] # Initial comment_data, refresh in loop to search all comments

        # Go to Facebook first to ensure you're logged in
        browser.get("https://www.facebook.com")
        time.sleep(5)

        # Check if we need to log in
        if "login" in browser.current_url:
            print("You need to manually log in once to save credentials")
            input("Press Enter after you've logged in...")

        # Now access the target content
        print(f"Accessing: {url}")
        browser.get(url)
        time.sleep(5)  # Give time for the page to fully load

        share_count, comment_count = get_share_count_and_num_comments(browser)
        static_content['share_count'] = share_count
        static_content['comment_count'] = comment_count

        click_require_button(browser) # Click all required buttons        


        print("Searching for comments to load after clicked button...")
        WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "[role='article']"))
        )

        # Loop to load all comments
        while True:
            # Before extract comment, press all 'Show more button' and 'Show all replies'

            click_reply_buttons(browser) # Display all comments in current layout
            print("Done dealing with '查看更多'and '查看回復' button.")

            comment_data = [] # Save the final comments which contains all
            # Find the comments section by looking for common patterns
            potential_selectors = [
                #"div.x78zum5 div[role='article']",
                "div[aria-label*='comment' i]",
                #"div.xdj266r div[role='article']",
                "div[role='article']"
            ]

            comments = []
            for selector in potential_selectors:
                try:
                    elements = browser.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        print(f"Found {len(elements)} comments using selector: {selector}")
                        comments = elements
                        break
                except Exception as e:
                    print(f"Selector {selector} failed: {e}")

            if not comments:
                print("Could not find comments with any of the predefined selectors")
                break  # Exit loop if no comments found

            # Extract comment data
            for i, comment in enumerate(comments, 1):
                try:
                    text_selectors = [
                        "div[dir='auto']",
                        "span[dir='auto']",
                        #"div.x1lliihq"
                    ]
                    comment_text = ""
                    for text_selector in text_selectors:
                        try:
                            elements = comment.find_elements(By.CSS_SELECTOR, text_selector)
                            print("elements of comment text: ", elements)
                            if elements:
                                #comment_text += elements[0].text
                                
                                for element in elements:
                                    comment_text += element.text + " " 

                                if comment_text:
                                    break
                                
                        except:
                            continue

                    name_selectors = [
                        #"a.x1i10hfl",
                        #"span.x3nfvp2",
                        "h3",
                        "a[role='link']"
                    ]
                    commenter_name = "Unknown User"
                    for name_selector in name_selectors:
                        try:
                            elements = comment.find_elements(By.CSS_SELECTOR, name_selector)
                            if elements:
                                potential_name = elements[0].text
                                if potential_name and len(potential_name) > 1:
                                    commenter_name = potential_name
                                    break
                        except:
                            continue

                    if comment_text:
                        comment_data.append({
                            "name": commenter_name,
                            "text": comment_text
                        })
                        print(f"Comment {i} by {commenter_name}: {comment_text}")

                except Exception as e:
                    print(f"Error extracting comment {i}: {e}")

            # Check if we need to load more comments
            try:
                load_more_button = WebDriverWait(browser, 20).until(
                    EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), '查看更多留言') or contains(text(), 'Load more comments')]"))
                )
                print("Found a 'Load more comments' button. Clicking...")
                browser.execute_script("arguments[0].click();", load_more_button) # Use JavaScript to click
                print("Done clicking.")
                time.sleep(3)  # Wait for new comments to load
                
            except NoSuchElementException:
                print("No 'Load more comments' button found. All comments loaded.")
                break  # Exit the loop

        
        return comment_data, static_content

    except TimeoutException:
        print("Timed out waiting for elements to load")
        return comment_data, static_content
    except Exception as e:
        print(f"An error occurred: {e}")
        return comment_data, static_content

    finally:
        print("Exit program!")
        browser.quit()

# Example usage
if __name__ == "__main__":

    chromedriver_path = r"C:\Users\User\laurence\drivers\chromedriver.exe"

    # Create a directory for the Chrome profile
    profile_directory = os.path.join(os.getcwd(), "chrome_profile")
    os.makedirs(profile_directory, exist_ok=True)
    
    reel_url = "https://www.facebook.com/reel/1712692176124613"
    comments, static_content = access_facebook_content(reel_url, profile_directory)

    with open('all_comments.json', 'w', encoding='utf-8') as f: # Save all comments to file
        json.dump(comments, f, ensure_ascii=False, indent=4)

    print("Data successfully all comments to all_comments.json")

    with open('static_content.json', 'w', encoding='utf-8') as f: # Save other static contents to file
        json.dump(static_content, f, ensure_ascii=False, indent=4)

    print("Data successfully static_content to static_content.json")