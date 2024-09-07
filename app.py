from flask import Flask, request, render_template
import pandas as pd
from textblob import TextBlob
import os

app = Flask(__name__)

# Paths to the datasets
UPLOAD_FOLDER = 'uploads'
STOCK_NEWS_FILE = 'stock_tweets.csv'
STOCK_DATA_FILE = 'stock_yfinance_data.csv'

# Function to initialize datasets
def initialize_datasets():
    # Check and load datasets
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    
    # File paths
    stock_news_path = os.path.join(UPLOAD_FOLDER, STOCK_NEWS_FILE)
    stock_data_path = os.path.join(UPLOAD_FOLDER, STOCK_DATA_FILE)
    
    # Load datasets
    stock_news_df = pd.read_csv(stock_news_path)
    stock_data_df = pd.read_csv(stock_data_path)
    
    # Clean and parse date columns
    stock_news_df['Date'] = pd.to_datetime(stock_news_df['Date'])
    stock_data_df['Date'] = pd.to_datetime(stock_data_df['Date'])
    
    # Check if datetime columns are timezone-aware and convert if needed
    if stock_news_df['Date'].dt.tz is None:
        stock_news_df['Date'] = stock_news_df['Date'].dt.tz_localize('UTC')
    else:
        stock_news_df['Date'] = stock_news_df['Date'].dt.tz_convert('UTC')
        
    if stock_data_df['Date'].dt.tz is None:
        stock_data_df['Date'] = stock_data_df['Date'].dt.tz_localize('UTC')
    else:
        stock_data_df['Date'] = stock_data_df['Date'].dt.tz_convert('UTC')
    
    return stock_news_df, stock_data_df

# Function to process and analyze data
def analyze_stock_data(company_name, start_date, end_date):
    stock_news_df, stock_data_df = initialize_datasets()

    # Convert start_date and end_date to Timestamp and localize to UTC
    start_date = pd.Timestamp(start_date).tz_localize('UTC')
    end_date = pd.Timestamp(end_date).tz_localize('UTC')

    # Filter data by company name and date range
    filtered_news_df = stock_news_df[
        (stock_news_df['StockName'].str.contains(company_name, case=False, na=False)) &
        (stock_news_df['Date'] >= start_date) &
        (stock_news_df['Date'] <= end_date)
    ]
    
    filtered_stock_data_df = stock_data_df[
        (stock_data_df['Date'] >= start_date) &
        (stock_data_df['Date'] <= end_date)
    ]
    
    if filtered_stock_data_df.empty:
        average_closing_price = "No data"
    else:
        average_closing_price = filtered_stock_data_df['Close'].mean()
    
    # Perform sentiment analysis
    sentiments = filtered_news_df['Tweet'].apply(lambda tweet: TextBlob(tweet).sentiment)
    
    positive_tweets = (sentiments.apply(lambda s: s.polarity > 0)).sum()
    negative_tweets = (sentiments.apply(lambda s: s.polarity < 0)).sum()
    neutral_tweets = (sentiments.apply(lambda s: s.polarity == 0)).sum()
    
    total_tweets = len(filtered_news_df)
    
    if total_tweets > 0:
        positive_percentage = (positive_tweets / total_tweets) * 100
        negative_percentage = (negative_tweets / total_tweets) * 100
        neutral_percentage = (neutral_tweets / total_tweets) * 100
    else:
        positive_percentage = negative_percentage = neutral_percentage = 0

    return {
        'average_closing_price': average_closing_price,
        'positive_percentage': positive_percentage,
        'negative_percentage': negative_percentage,
        'neutral_percentage': neutral_percentage,
    }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
@app.route('/process', methods=['POST'])
def process():
    company_name = request.form['company_name']
    start_date = request.form['start_date']
    end_date = request.form['end_date']
    
    result = analyze_stock_data(company_name, start_date, end_date)
    
    # Find the company name corresponding to the given stock name
    stock_news_df, _ = initialize_datasets()
    company_name_from_df = stock_news_df[
        stock_news_df['StockName'].str.contains(company_name, case=False, na=False)
    ]['CompanyName'].dropna().unique()
    
    # If there are multiple or no matches, handle accordingly
    if len(company_name_from_df) == 1:
        company_name_display = company_name_from_df[0]
    else:
        company_name_display = company_name  # Use the input name if no unique match
    
    return render_template('result.html', result=result, company_name=company_name_display)


if __name__ == '__main__':
    app.run(debug=True)
