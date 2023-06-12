from datetime import datetime, timedelta
import os
import json
from bs4 import BeautifulSoup as Soup
import requests
from flask import Flask, render_template, request
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
import io
import base64

app = Flask(__name__)

# Load the CSV data
data = pd.read_csv("Kottayam_2023-06-11.csv")

# Calculate room type statistics
room_type_stats = data.groupby('type').agg(
    max_price=('price', 'max'),
    min_price=('price', 'min'),
    mean_price=('price', 'mean'),
    avg_reviews=('ratings', 'mean')
).reset_index()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/stats')
def statistical_analysis():
    # Histogram
    hist_fig = plt.figure(figsize=(8, 6))
    hist_plot = hist_fig.add_subplot(111)
    sns.histplot(data['price'], ax=hist_plot, kde=True)
    hist_plot.set_xlabel('Price')
    hist_plot.set_ylabel('Frequency')
    hist_plot.set_title('Price Distribution')

    # Convert histogram figure to base64-encoded image
    hist_img_data = io.BytesIO()
    hist_fig.savefig(hist_img_data, format='png')
    hist_img_data.seek(0)
    hist_img_base64 = base64.b64encode(
        hist_img_data.getvalue()).decode('utf-8')

    # Pie chart for room types and prices
    pie_fig = plt.figure(figsize=(12, 6))
    pie_plot = pie_fig.add_subplot(111)
    pie_plot.pie(room_type_stats['mean_price'],
                 labels=room_type_stats['type'], autopct='%1.1f%%', startangle=90)
    pie_plot.axis('equal')
    pie_plot.set_title('Room Type Distribution')

    # Convert pie chart figure to base64-encoded image
    pie_img_data = io.BytesIO()
    pie_fig.savefig(pie_img_data, format='png')
    pie_img_data.seek(0)
    pie_img_base64 = base64.b64encode(pie_img_data.getvalue()).decode('utf-8')

    # Render the template with the base64-encoded image strings and room type statistics
    return render_template('stats.html', hist_img_base64=hist_img_base64, pie_img_base64=pie_img_base64, room_type_stats=room_type_stats)


@app.route('/predict', methods=['GET', 'POST'])
def model_prediction():
    if request.method == 'POST':
        selected_location = request.form['location']
        selected_type = request.form['type']

        # Perform your prediction based on the selected_location and selected_type
        # prediction_result = perform_prediction(selected_location, selected_type)

        # Render the template with the prediction result
        return render_template('predict.html', location=selected_location, room_type=selected_type, prediction_result="Your prediction result")

    return render_template('predict.html')


@app.route('/scrape', methods=['GET', 'POST'])
def scrape():
    if request.method == 'POST':
        # Get the entered location from the form
        selected_location = request.form['location']

        # Data collection and cleaning
        locations = [selected_location]
        
        def scrape_bookingdotcom(destination, checkin_date, checkout_date):
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36'
            }
            req = requests.get(
                f'https://www.booking.com/searchresults.en-us.html?ss={destination}&checkin_year_month={checkin_date}&checkout_year_month={checkout_date}', headers=headers)
            req.raise_for_status()
            return req.text

        def parse_bookingdotcom(html):
            soup = Soup(html, 'html.parser')
            hotel_list = soup.find_all(
                'div', {'class': 'sr_property_block'})
            data = []
            for hotel in hotel_list:
                name = hotel.find(
                    'span', {'class': 'sr-hotel__name'}).text.strip()
                price = hotel.find(
                    'div', {'class': 'bui-price-display__value'}).text.strip()
                ratings = hotel.find(
                    'div', {'class': 'bui-review-score__badge'}).text.strip()
                location = hotel.find(
                    'div', {'class': 'bui-link'}).text.strip()
                data.append({'name': name, 'price': price,
                             'ratings': ratings, 'location': location})
            return data

        combined_data = []
        for location in locations:
            for i in range(1, 8):
                checkin_date = (datetime.now() + timedelta(days=i)
                                ).strftime('%Y-%m-%d')
                checkout_date = (datetime.now() + timedelta(days=i+1)
                                 ).strftime('%Y-%m-%d')

                html = scrape_bookingdotcom(
                    location, checkin_date, checkout_date)
                parsed_data = parse_bookingdotcom(html)
                combined_data.extend(parsed_data)

        # Create a DataFrame from the scraped data
        scraped_df = pd.DataFrame(combined_data)

        # Combine the scraped data with the existing data
        combined_df = pd.concat([data, scraped_df])

        # Update the room type statistics
        room_type_stats = combined_df.groupby('type').agg(
            max_price=('price', 'max'),
            min_price=('price', 'min'),
            mean_price=('price', 'mean'),
            avg_reviews=('ratings', 'mean')
        ).reset_index()

        # Histogram
        hist_fig = plt.figure(figsize=(8, 6))
        hist_plot = hist_fig.add_subplot(111)
        sns.histplot(combined_df['price'], ax=hist_plot, kde=True)
        hist_plot.set_xlabel('Price')
        hist_plot.set_ylabel('Frequency')
        hist_plot.set_title('Price Distribution')

        # Convert histogram figure to base64-encoded image
        hist_img_data = io.BytesIO()
        hist_fig.savefig(hist_img_data, format='png')
        hist_img_data.seek(0)
        hist_img_base64 = base64.b64encode(
            hist_img_data.getvalue()).decode('utf-8')

        # Pie chart for room types and prices
        pie_fig = plt.figure(figsize=(12, 6))
        pie_plot = pie_fig.add_subplot(111)
        pie_plot.pie(room_type_stats['mean_price'],
                     labels=room_type_stats['type'], autopct='%1.1f%%', startangle=90)
        pie_plot.axis('equal')
        pie_plot.set_title('Room Type Distribution')

        # Convert pie chart figure to base64-encoded image
        pie_img_data = io.BytesIO()
        pie_fig.savefig(pie_img_data, format='png')
        pie_img_data.seek(0)
        pie_img_base64 = base64.b64encode(
            pie_img_data.getvalue()).decode('utf-8')

        # Render the template with the updated statistics and images
        #return render_template('stats.html', hist_img_base64=hist_img_base64, pie_img_base64=pie_img_base64, room_type_stats=room_type_stats)
        return render_template('stats.html', scraped_df)

    return render_template('scrape.html')


if __name__ == '__main__':
    app.run(debug=True)
