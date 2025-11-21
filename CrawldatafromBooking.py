import pyodbc
from playwright.sync_api import sync_playwright
from datetime import datetime  

def scrape_hotel_details(page, hotel_url: str):
    page.goto(hotel_url, timeout=20000)
    for _ in range(10):
        page.mouse.wheel(0, 2000)

    details = {}
    details['Facilities'] = page.locator('//*[@id="basiclayout"]/div[1]/div[7]/div/div[3]/div/div[4]/div/div[2]/div[2]/div/div/div[1]/div[2]').all_inner_texts()
    details['Comfort'] = page.locator('//*[@id="basiclayout"]/div[1]/div[7]/div/div[3]/div/div[4]/div/div[2]/div[4]/div/div/div[1]/div[2]').all_inner_texts()
    details['Staff'] = page.locator('//*[@id="basiclayout"]/div[1]/div[7]/div/div[3]/div/div[4]/div/div[2]/div[1]/div/div/div[1]/div[2]').all_inner_texts()
    details['FreeWifi'] = page.locator('//*[@id="basiclayout"]/div[1]/div[7]/div/div[3]/div/div[4]/div/div[2]/div[7]/div/div/div[1]/div[2]').all_inner_texts()
    details['ValueforMoney'] = page.locator('//*[@id="basiclayout"]/div[1]/div[7]/div/div[3]/div/div[4]/div/div[2]/div[5]/div/div/div[1]/div[2]').all_inner_texts()
    details['Cleanliness'] = page.locator('//*[@id="basiclayout"]/div[1]/div[7]/div/div[3]/div/div[4]/div/div[2]/div[3]/div/div/div[1]/div[2]').all_inner_texts()
    details['Location'] = page.locator('//*[@id="basiclayout"]/div[1]/div[7]/div/div[3]/div/div[4]/div/div[2]/div[6]/div/div/div[1]/div[2]').all_inner_texts()
    details['ScrapeDate'] = datetime.now().strftime('%Y-%m-%d')

    return details

def main():
    with sync_playwright() as p:
        page_url = f'https://www.booking.com/searchresults.vi.html?ss=TP.+H%E1%BB%93+Ch%C3%AD+Minh%2C+Khu+v%E1%BB%B1c+TP.+H%E1%BB%93+Ch%C3%AD+Minh%2C+Vi%E1%BB%87t+Nam&ssne=Vi%C3%AA%CC%A3t+Nam&ssne_untouched=Vi%C3%AA%CC%A3t+Nam&label=gen173nr-1BCAEoggI46AdIM1gEaPQBiAEBmAEquAEXyAEM2AEB6AEBiAIBqAIDuAKvqKy5BsACAdICJDdmMWE0YTAwLTVkNjQtNDYxMS05NTQyLTkxMjlmNzU3YTJiZNgCBeACAQ&sid=41be27dee23a9cd5a35e68b0f2dd2bd1&aid=304142&lang=vi&sb=1&src_elem=sb&src=index&dest_id=-3730078&dest_type=city&ac_position=0&ac_click_type=b&ac_langcode=vi&ac_suggestion_list_length=5&search_selected=true&search_pageview_id=b4ed79a4a4dd022e&ac_meta=GhBiNGVkNzlhNGE0ZGQwMjJlIAAoATICdmk6AVRAAEoAUAA%3D&checkin=10-11-2024&checkout=12-11-2024&group_adults=2&no_rooms=1&group_children=0'
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto(page_url, timeout=100000)

        # Đóng cửa sổ đăng nhập để tránh lỗi khi cào dữ liệu
        popup_close_button = page.locator('//button[contains(text(), "Đăng nhập hoặc đăng ký")]')
        if popup_close_button.is_visible():
            popup_close_button.click()
            page.wait_for_timeout(5000)

        hotels_list = []
        scraped_hotel_urls = set()  # Lấy các khách sạn duy nhất theo url
        while len(hotels_list) < 10000:
            hotels = page.locator('//div[@data-testid="property-card"]').all()
            
            for hotel in hotels:
                hotel_url = hotel.locator('a[data-testid="title-link"]').get_attribute('href')
                # Kiểm tra nếu khách sạn đã được cào 
                if hotel_url in scraped_hotel_urls:    
                    continue  # Bỏ qua khách sạn trùng

                hotel_dict = {}
                hotel_dict['HotelName'] = hotel.locator('//div[@data-testid="title"]').inner_text()
                hotel_dict['Price'] = hotel.locator('//span[@data-testid="price-and-discounted-price"]').inner_text()
                hotel_dict['Score'] = hotel.locator('//div[@data-testid="review-score"]/div[1]').inner_text()
                hotel_dict['AvgReview'] = hotel.locator('//div[@data-testid="review-score"]/div[2]/div[1]').inner_text()
                hotel_dict['ReviewsCount'] = hotel.locator('//div[@data-testid="review-score"]/div[2]/div[2]').inner_text()
                location_text = hotel.locator('//span[@data-testid="address"]').inner_text()
                hotel_dict['City'] = location_text.split(',')[-1].strip()


                # Gọi hàm truy cập url từng khách sạn và thêm thông tin cho từng khách sạn
                hotel_page = browser.new_page()
                details = scrape_hotel_details(hotel_page, hotel_url)
                hotel_dict.update(details)
                hotel_page.close()

                hotels_list.append(hotel_dict)
                scraped_hotel_urls.add(hotel_url)

            # Cuộn xuống để tải thêm khách sạn
            page.mouse.wheel(0, 5000)
            page.wait_for_timeout(1000)
            print(f'Total hotels scraped so far: {len(hotels_list)}')

            # Kiểm tra và nhấn vào nút Tải thêm kết quả
            load_more_button = page.locator('button:has-text("Tải thêm kết quả")')
            if load_more_button.is_visible():
              load_more_button.click()
              print("Đã tải thêm kết quả")

        # Kết nối đến cơ sở dữ liệu SQL Azure  
        server = 'nhathong-1611.database.windows.net'
        database = 'Booking'
        username = 'nhathong-1611'
        password = 'LCG4FAVQ@Pv3cFw'
        driver = '{ODBC Driver 17 for SQL Server}'

        conn = pyodbc.connect(f'DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password}', timeout=30)
        cursor = conn.cursor()

        for hotel in hotels_list:
            facilities = ', '.join(hotel['Facilities']) if hotel['Facilities'] else ''
            comfort = ', '.join(hotel['Comfort']) if hotel['Comfort'] else ''
            staff = ', '.join(hotel['Staff']) if hotel['Staff'] else ''
            free_wifi = ', '.join(hotel['FreeWifi']) if hotel['FreeWifi'] else ''
            value_for_money = ', '.join(hotel['ValueforMoney']) if hotel['ValueforMoney'] else ''
            cleanliness = ', '.join(hotel['Cleanliness']) if hotel['Cleanliness'] else ''
            location = ', '.join(hotel['Location']) if hotel['Location'] else ''

            insert_query = """
                INSERT INTO Hotel_cleaned
                (HotelName, Price, Score, AvgReview, ReviewsCount, City, ScrapeDate, Facilities, Comfort, Staff, FreeWifi, ValueforMoney, Cleanliness, Location) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            cursor.execute(insert_query, 
                           hotel['HotelName'], hotel['Price'], hotel['Score'], 
                           hotel['AvgReview'], hotel['ReviewsCount'], 
                           hotel.get('City', ''), 
                           hotel.get('ScrapeDate', ''), 
                           facilities, comfort, staff, free_wifi, value_for_money, cleanliness, location)

        conn.commit()
        cursor.close()
        conn.close()
        browser.close()

if __name__ == "__main__":
    main()