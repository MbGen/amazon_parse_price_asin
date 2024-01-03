import peewee
import requests
import re
import uvicorn
import logging

from fastapi import FastAPI
from starlette.responses import RedirectResponse
from bs4 import BeautifulSoup
from pydantic import BaseModel

from FastAPITask.models import Product

app = FastAPI()
logger = logging.getLogger(__name__)


class ErrorResponse(BaseModel):
    type: str
    text: str


class ProductResponse(BaseModel):
    price: float | None = None
    currency: str | None = None
    name: str | None = None
    description: str | None = None


class AmazonScraper:
    AMAZON_URL = 'https://www.amazon.com/dp/'

    @property
    def headers(self):
        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive",
            "Cookie": "",
            "Host": "www.amazon.com",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "TE": "trailers",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0"
        }
        return headers

    def generate_url_for_asin(self, asin: str) -> str:
        return self.AMAZON_URL + asin

    def find_currency(self, text) -> str | None:
        for ix, char in enumerate(text):
            if char.isalnum():
                return text[:ix]
        return None

    def find_price_and_currency(self, soup) -> tuple[float, str]:
        parent_span = soup.find('span', class_='apexPriceToPay')
        price_text = parent_span.find('span').text

        price_regex = re.compile(r'\d+\.\d+|\d+')
        price = re.findall(price_regex, price_text)[0]
        return float(price), self.find_currency(text=price_text)

    def save_product_information_to_db(self, model: peewee.Model, data: dict):
        product = model(**data)
        product.save()

    def parse(self, asin):
        product_url = self.generate_url_for_asin(asin)
        response = requests.get(product_url, headers=self.headers)

        if response.ok:
            soup = BeautifulSoup(response.text, 'html.parser')

            try:
                price, currency = self.find_price_and_currency(soup)
                product_price_response = ProductResponse(price=price, currency=currency).model_dump()

                self.save_product_information_to_db(model=Product, data=product_price_response)

                return product_price_response

            except ValueError as exc:
                logger.error(repr(exc.errors()))
                return exc.errors()
            except peewee.IntegrityError as err:
                logger.error(err)

            return ErrorResponse(type='Server', text='Error with getting data')
        else:
            return ErrorResponse(type='Server', text='Unknown error')


@app.get('/')
async def index():
    return RedirectResponse(url='/docs')


@app.get('/get_price/{asin}')
async def get_price(asin: str):
    """
    Extracts product information from Amazon by ASIN.
    """
    scraper = AmazonScraper()
    response = scraper.parse(asin)
    return response


if __name__ == '__main__':
    uvicorn.run(app, host='localhost', port=8000, log_config='log_conf.yaml')

