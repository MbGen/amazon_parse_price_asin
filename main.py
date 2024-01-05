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
    product_asin: str
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
            "Cookie": "session-id=133-9248822-6701907; session-id-time=2082787201l; i18n-prefs=USD; csm-hit=tb:s-PMNMT2R1CD6WW2BWQ8F2|1704286535472&t:1704286536953&adb:adblk_yes; ubid-main=132-7304988-2968536; sp-cdn=\"L5Z9:UA\"; session-token=zUdjYWc3DkpgGS8qZ1kSpdy2etyj7KLQenSFMd3DdyD0+7w55TiGat57KzsdfX3BEQ/6y6S031oV3Mkdq6Jg9Q9dF+hIp8OYHSLy6N0Cknuvdx5Cgt2oGx7tweMUgOaD0Y788CXABR0/GrJssg5AM8H6hTnrGDO1aEBQFa0MesnbrHOeBK4Evzh/N00HpslBe27vNv0BDQixrFh4q96pvAUymO5tySSoO4oph+ClHCN9BV/LZr/j+as7hCoOiEtljdD9wLiG6rjauys99uY2RV/D+en7QjSSXfr2fSB+0SKNLaB4xgld09w4EYRHQEaEQM6LZvNwDvPX5NKFb9rMf6h6Eu5ni2Sq; lc-main=en_US; skin=noskin",
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

    def find_price_and_currency(self, soup) -> tuple[float, str] | tuple[None, None]:
        parent_span = soup.find('span', class_='apexPriceToPay')

        if parent_span is None:
            parent_span = soup.find('span', class_='priceToPay')
            if parent_span is None:
                return None, None

        price_text = parent_span.find('span').text

        price_regex = re.compile(r'\d+\.\d+|\d+')
        price = re.findall(price_regex, price_text)[0]

        return float(price), self.find_currency(text=price_text)

    def save_product_information_to_db(self, model: peewee.Model, data: dict):
        product = model(**data)
        query = model.select().where(model.product_asin == data['product_asin'])
        if query.exists():
            model.update(**data)
        else:
            product.save()

    def parse(self, asin):
        product_url = self.generate_url_for_asin(asin)
        response = requests.get(product_url, headers=self.headers)

        if response.ok:
            soup = BeautifulSoup(response.text, 'html.parser')

            try:
                price, currency = self.find_price_and_currency(soup)
                if price is not None and currency is not None:

                    product_price_response = ProductResponse(price=price,
                                                             currency=currency,
                                                             product_asin=asin).model_dump()

                    self.save_product_information_to_db(model=Product, data=product_price_response)

                    return product_price_response

                return ErrorResponse(type='Error', text='Product is unavailable or has no price')
            except ValueError as exc:
                logger.error(repr(exc.errors()))
                return exc.errors()
            except peewee.IntegrityError as err:
                logger.error(err)

            return ErrorResponse(type='Error', text='Error with getting data')
        else:
            return ErrorResponse(type='Error', text='Unknown error')


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

