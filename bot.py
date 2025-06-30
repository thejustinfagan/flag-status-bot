import os
import time
import logging
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw, ImageFont
import tweepy
from tenacity import retry, stop_after_attempt, wait_exponential

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class TwitterFlagBot:
    def __init__(self):
        self.setup_twitter_client()
        self.setup_scraper()

    def setup_twitter_client(self):
        """Initialize Twitter API client"""
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
        """Initialize web scraper"""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; FlagBot/1.0)'
        })

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2))
    def scrape_flag_status(self):
        """Scrape current flag status"""
        response = self.session.get("https://starsandstripesdaily.org", timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        page_text = soup.get_text().lower()
        if 'flag status: half' in page_text:
            return 'HALF-STAFF'
        elif 'flag status: full' in page_text:
            return 'FULL'
        return 'UNKNOWN'

    def create_flag_image(self, status):
        """Generate flag status image"""
        width, height = 1200, 675
        img = Image.new('RGB', (width, height))
        draw = ImageDraw.Draw(img)
        # Patriotic gradient background
        for y in range(height):
            ratio = y / height
            if ratio < 0.33:
                color = (220, 50, 50)
            elif ratio < 0.67:
                color = (255, 255, 255)
            else:
                color = (50, 50, 220)
            draw.line([(0, y), (width, y)], fill=color)
        # Add text
        try:
            font = ImageFont.truetype("arial.ttf", 64)
        except:
            font = ImageFont.load_default()
        text = f"🇺🇸 US FLAG: {status} 🇺🇸"
        x, y = width // 2, height // 2
        # Text with outline
        for dx in [-2, 0, 2]:
            for dy in [-2, 0, 2]:
                if dx != 0 or dy != 0:
                    draw.text((x + dx, y + dy), text, font=font, fill='black', anchor='mm')
        draw.text((x, y), text, font=font, fill='white', anchor='mm')
        img.save('flag_status.png')
        return 'flag_status.png'

    def post_tweet(self, status):
        """Post tweet with flag status"""
        try:
            image_path = self.create_flag_image(status)
            current_time = datetime.now().strftime("%B %d, %Y")
            tweet_text = f"🇺🇸 US Flag Status Update for {current_time}\n\nStatus: {status}\n\n#AmericanFlag #USA #Patriotic"
            media = self.twitter_client.media_upload(image_path)
            self.twitter_client.update_status(
                status=tweet_text,
                media_ids=[media.media_id]
            )
            logging.info(f"Successfully posted tweet with status: {status}")
        except Exception as e:
            logging.error(f"Failed to post tweet: {e}")
            raise

    def run(self):
        """Main bot execution"""
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
