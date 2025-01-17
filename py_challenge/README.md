## Car Data Scraper

## Challenge Overview
The **Car Data Scraper** is a python based application designed to collect specific vehicle information from [Peter Stevens Motorworld](https://www.peterstevensmotorworld.com.au/) and organize it. The application is designed to run daily on a virtual server(pythonanywhere/cs50 in my case). It includes  error handling mechanisms.

---
## Requirements

### System Requirements
- **Python Language**: The application is written in Python and requires a Python environment to run.
- **Virtual Server**: Ensure the virtual server is configured to run Python applications and supports scheduled tasks (e.g., cron jobs).


## Error Handling
The application incorporates robust error-handling features:
- **Retries**: Implements retry logic for transient errors.
- **Sleeps**: Sleeps for a specified amount of time before making a new request.

---


## Features
- **Daily Automation**: The scraper runs every day to fetch updated data.
- **Data Extraction**: Collects the following details:
  - Name (year, make, model)
  - Make
  - Model
  - Build Date
  - Odometer
  - Body Type
  - Fuel Type
  - Transmission
  - Number of Seats
  - Provider
  - Link to the Car
  - Other Specifications
  - State
  - VIN (Vehicle Identification Number)
- **Data Sharing**: Saves data on a platform accessible to your team.
- **Error Handling**: Built-in mechanisms to log and handle errors effectively.

---

### Overview

This is a program that automatically collects information about cars from the Peter Stevens Motor World website. The program does the following:

1. Visits the car dealership website and counts how many pages of cars there are
2. Goes through each page and collects details about every car it finds, including:
   - Basic info (make, model, year)
   - Technical details (mileage, fuel type, transmission)
   - Price and location
   - Identification numbers (VIN, registration)

The program automatically goes to the next page and waits between page visits. As it collects the information, it saves it in two ways:
- As a spreadsheet (CSV file) that you can open in Excel
- In a database (SQLite)  and saves as *.db* filetype can beimported into any DBMS tool.

*The whole process is automated, so once you start it, it does all the work on its own and tells you when it's done. If anything goes wrong, it lets you know what happened and tries to save any information it already collected.*



### About The Code

Following are the libraries used in the code:

- `requests`: For making HTTP requests to the website.
- `bs4`: For parsing HTML content.
- `json`: For working with JSON data.
- `pandas`: For data manipulation and analysis.
- `logging`: For logging error messages.
- 'datetime': For working with dates and times.
- 'time': For working with time-related functions.
- sqlite3: For working with SQLite databases.

---


## Setup Instructions

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/yourusername/car-data-scraper.git
   cd car-data-scraper
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure the Application**:
   - Edit `config.py` to specify platform details for sharing data (e.g., database or file storage system).
   - Add virtual server scheduling configurations.

4. **Run the Application**:
   ```bash
   python main.py
   ```

5. **Set Up Daily Execution**:
   - Use a task scheduler like `cron` on Linux or Task Scheduler on Windows.
   - Example cron job:
     ```bash
     0 2 * * * /path/to/python /path/to/car-data-scraper/main.py
     ```

---