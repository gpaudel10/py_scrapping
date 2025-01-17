import requests
from bs4 import BeautifulSoup
import json
import pandas as pd
from datetime import datetime
import time
from typing import List, Dict
import sqlite3
from sqlite3 import Error

class CarScraper:
    def __init__(self):
        self.base_url = "https://www.peterstevensmotorworld.com.au"
        self.search_url = f"{self.base_url}/search/new-used-and-demo-cars"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.csv_headers = [
            'name', 'year', 'make', 'model', 'badge', 'series', 
            'build_date', 'odometer', 'body_type', 'fuel', 
            'transmission', 'transmission_type', 'seats', 'doors',
            'drive_type', 'provider', 'location', 'city', 'state',
            'price', 'price_type', 'car_type', 'stock_number',
            'vin', 'rego', 'status', 'colour', 'link_to_the_car'
        ]
        self.db_connection = None
        self.db_cursor = None

    def get_page_content(self, url: str, page: int = 1) -> str:
        """Fetch page content with retry mechanism"""
        full_url = f"{url}?page={page}"
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                response = requests.get(full_url, headers=self.headers, timeout=10)
                response.raise_for_status()
                return response.text
            except requests.RequestException as e:
                if attempt == max_retries - 1:
                    print(f"Failed to fetch {full_url} after {max_retries} attempts: {str(e)}")
                    return None
                time.sleep(2 * (attempt + 1))
        return None

    def extract_car_data(self, html_content: str) -> List[Dict]:
        """Extract car data from the embedded JSON in the page."""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            next_data = soup.find('script', {'id': '__NEXT_DATA__'})
            
            if not next_data:
                print("No __NEXT_DATA__ found")
                return []

            data = json.loads(next_data.string)
            car_results = (data.get('props', {})
                          .get('pageProps', {})
                          .get('serverState', {})
                          .get('initialResults', {})
                          .get('Car_production:custom_rank:desc', {})
                          .get('results', []))

            if not car_results:
                print("No car results found in data structure")
                return []

            hits = car_results[0].get('hits', [])
            print(f"Found {len(hits)} cars on current page")

            cars = []
            for car in hits:
                try:
                    # slug is used to construct the car url
                    car_slug = car.get('slug', '').strip()
                    car_url = f"{self.base_url}/vehicle/{car_slug}" if car_slug else ''
                    
                    car_data = {
                        # requirements of data
                        'name': car.get('name'),
                        'make': car.get('make'),
                        'model': car.get('model'),
                        'badge': car.get('badge'),
                        'series': car.get('series'),
                        'year': car.get('year'),
                        'colour': car.get('colour'),
                        'status': car.get('status'),
                        'link_to_the_car': car_url,
                        
                        # specifications
                        'build_date': car.get('build_date'),
                        'odometer': car.get('km'),
                        'body_type': car.get('body'),
                        'fuel': car.get('fuel'),
                        'transmission': car.get('trans'),
                        'transmission_type': car.get('simple_transmission'),
                        'seats': car.get('seats'),
                        'doors': car.get('doors'),
                        'drive_type': car.get('drive'),
                        
                        # other info
                        'provider': car.get('dealership_name'),
                        'location': car.get('location_name'),
                        'city': car.get('city'),
                        'state': car.get('state'),
                        
                        # price and status
                        'price': car.get('price'),
                        'price_type': car.get('price_type'),
                        'car_type': car.get('car_type'),
                        
                        # numbers / vehicle identification number
                        'stock_number': car.get('stocknum'),
                        'vin': car.get('vin'),
                        'rego': car.get('regplate'),
                    }
                    cars.append(car_data)
                    print(f"Extracted: {car_data['year']} {car_data['make']} {car_data['model']} ({car_data['stock_number']})")
                except Exception as e:
                    print(f"Error processing individual car: {str(e)}")
                    continue

            return cars
        
        except Exception as e:
            print(f"Error extracting car data: {str(e)}")
            import traceback
            traceback.print_exc()
            return []

    def get_total_pages(self, html_content: str) -> int:
        """Extract total number of pages from the JSON data"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            next_data = soup.find('script', {'id': '__NEXT_DATA__'})
            
            if next_data:
                data = json.loads(next_data.string)
                car_results = (data.get('props', {})
                              .get('pageProps', {})
                              .get('serverState', {})
                              .get('initialResults', {})
                              .get('Car_production:custom_rank:desc', {})
                              .get('results', []))
                
                if car_results:
                    total_hits = car_results[0].get('nbHits', 0)
                    hits_per_page = car_results[0].get('hitsPerPage', 20)
                    return -(-total_hits // hits_per_page) 
            
            return 1
        except Exception as e:
            print(f"Error getting total pages: {str(e)}")
            return 1

    def scrape_cars(self) -> List[Dict]:
        """Main scraping function"""
        all_cars = []
        
        # to get first page and total pages
        first_page_content = self.get_page_content(self.search_url)
        if not first_page_content:
            return all_cars

        total_pages = self.get_total_pages(first_page_content)
        print(f"Found {total_pages} pages to scrape")

        # extracting from the first page
        cars = self.extract_car_data(first_page_content)
        all_cars.extend(cars)

        # for other pages
        for page in range(2, total_pages + 1):
            print(f"Scraping page {page}/{total_pages}")
            page_content = self.get_page_content(self.search_url, page)
            if page_content:
                cars = self.extract_car_data(page_content)
                all_cars.extend(cars)
            time.sleep(2)  

        return all_cars

    def setup_database(self, db_file: str = 'car_data.db'):
        """Create a database connection and setup tables"""
        try:
            self.db_connection = sqlite3.connect(db_file)
            self.db_cursor = self.db_connection.cursor()
            
            # create cars table
            create_table_sql = """
            CREATE TABLE IF NOT EXISTS cars (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                year INTEGER,
                make TEXT,
                model TEXT,
                badge TEXT,
                series TEXT,
                build_date TEXT,
                odometer TEXT,
                body_type TEXT,
                fuel TEXT,
                transmission TEXT,
                transmission_type TEXT,
                seats INTEGER,
                doors INTEGER,
                drive_type TEXT,
                provider TEXT,
                location TEXT,
                city TEXT,
                state TEXT,
                price REAL,
                price_type TEXT,
                car_type TEXT,
                stock_number TEXT,
                vin TEXT,
                rego TEXT,
                status TEXT,
                colour TEXT,
                link_to_the_car TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
            self.db_cursor.execute(create_table_sql)
            self.db_connection.commit()
            print(f"successfully connected to database.: {db_file}")
            
        except Error as e:
            print(f"Error setting up database: {e}")
            if self.db_connection:
                self.db_connection.close()
            raise

    def save_to_database(self, cars: List[Dict]):
        """Save scraped data to sqlite database"""
        if not self.db_connection:
            self.setup_database()

        try:
            # for insert query to the database
            columns = ', '.join(self.csv_headers)
            placeholders = ', '.join(['?' for _ in self.csv_headers])
            insert_sql = f"INSERT INTO cars ({columns}) VALUES ({placeholders})"

            # data to insert in the database
            car_data = []
            for car in cars:
                row = []
                for header in self.csv_headers:
                    value = car.get(header, '')
                    # make  empty strings to none for numeric fields
                    if header in ['year', 'seats', 'doors', 'price'] and value == '':
                        value = None
                    row.append(value)
                car_data.append(tuple(row))

            # start inserting data
            self.db_cursor.executemany(insert_sql, car_data)
            self.db_connection.commit()
            
            print(f"\nSuccessfully saved {len(cars)} cars to database")
            
            # checking 
            self.db_cursor.execute("SELECT COUNT(*) FROM cars")
            total_cars = self.db_cursor.fetchone()[0]
            
            self.db_cursor.execute("SELECT make, COUNT(*) as count FROM cars GROUP BY make ORDER BY count DESC LIMIT 5")
            top_makes = self.db_cursor.fetchall()
            
            print(f"\nDatabase Statistics:")
            print(f"Total cars in database: {total_cars}")
            print("\nTop 5 makes:")
            for make, count in top_makes:
                print(f"{make}: {count} cars")
            
        except Error as e:
            print(f"Error saving to database: {e}")
            self.db_connection.rollback()

    def save_to_csv(self, cars: List[Dict], filename: str = None):
        """Save scraped data to CSV file"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'cars_data_{timestamp}.csv'

        try:
            df = pd.DataFrame(cars)
            # fill empty strings if needed
            for col in self.csv_headers:
                if col not in df.columns:
                    df[col] = ''
            df = df[self.csv_headers]
            df.to_csv(filename, index=False)
            print(f"data saved to {filename}")
            print(f"total cars saved: {len(df)}")
        except Exception as e:
            print(f"Error saving to csv: {str(e)}")
            import traceback
            traceback.print_exc()

    def close_database(self):
        """Close the database connection"""
        if self.db_connection:
            self.db_connection.close()
            print("database connection is closed")

def main():
    scraper = CarScraper()
    try:
        print("starting car data scraping...")
        cars = scraper.scrape_cars()
        print(f"scraped {len(cars)} cars")
        
        # save to csv
        scraper.save_to_csv(cars)
        
        # save to database
        scraper.save_to_database(cars)
        
    finally:
        scraper.close_database()

if __name__ == "__main__":
    main()