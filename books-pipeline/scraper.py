import os
import time
import requests
from bs4 import BeautifulSoup
import pandas as pd

# non-interactive backend for headless server execution
import matplotlib
matplotlib.use('Agg')
import seaborn as sns
import matplotlib.pyplot as plt

def run_scraper():
    print("🚀 Starting automated scraping pipeline...")
    base_url = "https://books.toscrape.com/catalogue/page-{}.html"
    all_books = []

    for page in range(1, 51):
        url = base_url.format(page)
        try:
            response = requests.get(url, timeout=10)
            if response.status_code != 200:
                print(f"Reached end of catalog at page {page}.")
                break
                
            soup = BeautifulSoup(response.text, 'html.parser')
            books = soup.find_all('article', class_='product_pod')
            if not books:
                break
                
            for book in books:
                title = book.h3.a['title']
                price_str = book.find('p', class_='price_color').text.strip()
                price = float(price_str.replace('£', '').replace('Â', ''))
                availability = book.find('p', class_='instock availability').text.strip()
                rating_classes = book.p['class']
                rating = rating_classes[1] if len(rating_classes) > 1 else 'Unrated'
                
                all_books.append({
                    'Title': title,
                    'Price_GBP': price,
                    'Availability': availability,
                    'Rating': rating
                })
            time.sleep(0.3)
        except Exception as e:
            print(f"Error scraping page {page}: {e}")
            break

    # Convert and Clean Data
    df = pd.DataFrame(all_books)
    initial_count = len(df)
    df = df.drop_duplicates(subset=['Title']).reset_index(drop=True)
    print(f"Processed {len(df)} unique records (removed {initial_count - len(df)} duplicates).")

    # Feature Engineering
    rating_map = {'One': 1, 'Two': 2, 'Three': 3, 'Four': 4, 'Five': 5}
    df['Rating_Score'] = df['Rating'].map(rating_map)
    df['In_Stock'] = df['Availability'].str.contains('In stock').astype(int)

    # Save Cleaned CSV
    os.makedirs('data', exist_ok=True)
    csv_path = 'data/books_cleaned.csv'
    df.to_csv(csv_path, index=False)
    print(f"Dataset successfully saved to {csv_path}")

    # Generate & Save EDA Visualizations
    print("📊 Generating automated EDA plots...")
    sns.set_theme(style="whitegrid")
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    sns.histplot(df['Price_GBP'], kde=True, ax=axes[0], color='teal', bins=25)
    axes[0].set_title('Book Price Distribution (£)', fontsize=13, fontweight='bold')

    sns.boxplot(x='Rating', y='Price_GBP', data=df, order=['One', 'Two', 'Three', 'Four', 'Five'], palette='crest', ax=axes[1])
    axes[1].set_title('Price vs Star Rating', fontsize=13, fontweight='bold')

    plt.tight_layout()
    plot_path = 'data/price_distribution.png'
    plt.savefig(plot_path, dpi=300)
    print(f"EDA chart successfully saved to {plot_path}")

if __name__ == "__main__":
    run_scraper()
