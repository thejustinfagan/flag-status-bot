import os
import time
import logging
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import tweepy
from tenacity import retry, stop_after_attempt, wait_exponential

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class TwitterFlagBot:
    def __init__(self):
        self.setup_twitter_client()
        self.setup_scraper()

    def setup_twitter_client(self):
        auth = tweepy.OAuthHandler(
            os.environ['TWITTER_API_KEY'],
            os.environ['TWITTER_API_SECRET']
        )
        auth.set_access_token(
            os.environ['TWITTER_ACCESS_TOKEN'],
            os.environ['TWITTER_ACCESS_SECRET']
        )
        self.twitter_client = tweepy.API(auth, wait_on_rate_limit=True)

    def setup_scraper(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; FlagBot/1.0)'
        })

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2))
    def scrape_flag_status(self):
        response = self.session.get("https://starsandstripesdaily.org", timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        page_text = soup.get_text().lower()
        if 'flag status: half' in page_text:
            return 'HALF-STAFF'
        elif 'flag status: full' in page_text:
            return 'FULL'
        return 'UNKNOWN'

    def post_tweet(self, status):
        try:
            current_time = datetime.now().strftime("%B %d, %Y %I:%M %p")
            tweet_text = f"🇺🇸 US Flag Status Update for {current_time}\n\nStatus: {status}\n\n#AmericanFlag #USA #Patriotic"
            self.twitter_client.update_status(status=tweet_text)
            logging.info(f"Successfully posted tweet with status: {status}")
        except Exception as e:
            logging.error(f"Failed to post tweet: {e}")
            raise

    def run(self):
        try:
            logging.info("Starting flag bot execution")
            status = self.scrape_flag_status()
            logging.info(f"Scraped flag status: {status}")
            self.post_tweet(status)
            logging.info("Bot execution completed successfully")
        except Exception as e:
            logging.error(f"Bot execution failed: {e}")
            raise

if __name__ == "__main__":
    bot = TwitterFlagBot()
    bot.run()

