# datacollection and cleaning
import requests
from bs4 import BeautifulSoup as Soup
import pandas as pd
import json
import os
from datetime import datetime, timedelta
locations = ["Delhi"]
# Function to scrape data from Booking.com


def scrape_bookingdotcom(destination, checkin_date, checkout_date):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36'
    }
    req = requests.get(
        f"https://www.booking.com/searchresults.en-gb.html?ss={destination}&checkin={checkin_date}&checkout={checkout_date}&offset==0",
        headers=headers).text
    soup = Soup(req, 'html.parser')
    ap = soup.find("ol", {"class": "a8b500abde"}).text

    df = pd.DataFrame(columns=["price", "location",
                      "distance", "amenities", "ratings", "type"])
    for pages in range(0, int(ap[len(ap) - 1])):
        req = requests.get(
            f"https://www.booking.com/searchresults.en-gb.html?ss={destination}&checkin={checkin_date}&checkout={checkout_date}&offset=={pages * 25}",
            headers=headers).text
        soup = Soup(req, 'html.parser')
        apts = soup.find_all("div", {"class": "d20f4628d0"})
        rows = []

        for a in range(0, len(apts)):
            obj = {}

            try:
                obj["price"] = apts[a].find(
                    "span", {"class": "fcab3ed991 fbd1d3018c e729ed5ab6"}).text
            except:
                obj["price"] = None

            try:
                obj["distance"] = apts[a].find(
                    "span", {"class": "cb5ebe3ffb"}).text
            except:
                obj["distance"] = None

            try:
                ap1 = apts[a].find('a', href=True)
                link = ap1['href']
                req1 = requests.get(link, headers=headers).text
                soup2 = Soup(req1, 'html.parser')
                obj["amenities"] = soup2.find(
                    "div", {"class": "e5e0727360"}).text
            except:
                obj["amenities"] = None

            try:
                obj["ratings"] = apts[a].find(
                    "div", {"class": "b5cd09854e d10a6220b4"}).text
            except:
                obj["ratings"] = None

            try:
                obj["type"] = apts[a].find(
                    "span", {"class": "df597226dd"}).text
            except:
                obj["type"] = None

            try:
                obj["location"] = apts[a].find(
                    "span", {"class": "f4bd0794db b4273d69aa"}).text
            except:
                obj["location"] = None

            rows.append(obj)

        df = pd.concat([df, pd.DataFrame(rows)])

    # Data cleaning
    df["price"] = df["price"].str.replace(r"₹", "")
    df["price"] = df["price"].str.replace(r" ", "")
    df["price"] = df["price"].str.replace(r",", "")
    df["price"] = df["price"].str.strip()
    df['price'] = pd.to_numeric(df['price'])
    df['ratings'] = pd.to_numeric(df['ratings'], errors='coerce')
    df['ratings'] = df['ratings'].fillna(df['ratings'].mean())

    return df


# Load scraped locations from JSON file
# JSON file to store scraped locations
scraped_locations_file = "scraped_locations.json"
try:
    with open(scraped_locations_file, "r") as file:
        scraped_locations = set(json.load(file))
except FileNotFoundError:
    scraped_locations = set()

# Take user input for the location, check-in date, and check-out date
user_location = input("Enter the city name: ").strip().capitalize()
current_date = datetime.now().strftime("%Y-%m-%d")
checkin_date = current_date
checkout_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

# Check if location has already been scraped
if user_location.lower() in map(str.lower, scraped_locations):
    print(f"Skipping {user_location}. Already scraped.")
else:
    # Scrape data for the location
    df = scrape_bookingdotcom(user_location, checkin_date, checkout_date)

    # Update the set of scraped locations
    scraped_locations.add(user_location)

    # Save the data to a CSV file with current date in the filename
    csv_filename = f"{user_location}_{current_date}.csv"
    df.to_csv(csv_filename, index=False)

    print(f"Scraped and saved data for {user_location}.")
for location in locations:
    if location.lower() not in map(str.lower, scraped_locations):
        # Scrape data for the location
        df = scrape_bookingdotcom(location, checkin_date, checkout_date)

        # Update the set of scraped locations
        scraped_locations.add(location)

        # Save the data to a CSV file with current date in the filename
        csv_filename = f"{location}_{current_date}.csv"
        df.to_csv(csv_filename, index=False)

        print(f"Scraped and saved data for {location}.")

# Save the updated set of scraped locations to the JSON file
with open(scraped_locations_file, "w") as file:
    json.dump(list(scraped_locations), file)

# Combine all CSV files into a single dataframe
combined_df = pd.DataFrame()
for location in list(scraped_locations):
    csv_filename = f"{location}_{current_date}.csv"
    if os.path.isfile(csv_filename):
        df = pd.read_csv(csv_filename)
        combined_df = pd.concat([combined_df, df])

# Save the combined dataframe to a CSV file with current date in the filename
final_csv_filename = f"combined_{current_date}.csv"
combined_df.to_csv(final_csv_filename, index=False)

print("Scraping completed.")
