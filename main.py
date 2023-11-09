import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pyppeteer import launch
import json

class Item(BaseModel):
    url: str


async def get_content(link):
    browser = await launch(headless=True, options={'args': ['--no-sandbox']})
    page = await browser.newPage()
    await page.goto(link)
    html_content = await page.content()
    await browser.close()
    return html_content


async def parse_apartment(link):
    html_content = await get_content(link)
    if html_content is None:
        raise Exception('HTML is empty. No such apartment')
    if html_content:
        soup = BeautifulSoup(html_content, 'html.parser')
        offer_short_desc = soup.find('div', class_='offer__short-description').findAll('div', class_='offer__info-item')

        offer_parameters = soup.find('div', class_='offer__parameters').findAll('dl')
        options = soup.find('div', class_='a-options-text a-text-white-spaces').text.strip() if soup.find('div', class_='a-options-text a-text-white-spaces') else None
        text = soup.find('div', class_='a-text a-text-white-spaces').text.strip() if soup.find('div', class_='a-text a-text-white-spaces') else None
        result_dict = {}

        for div_element in offer_short_desc:
            data_name = div_element.get('data-name')
            value_element = div_element.find('div', class_='offer__advert-short-info')

            if data_name and value_element:
                value = value_element.text.strip()
                result_dict[data_name] = value

        for dl_element in offer_parameters:
            dt_element = dl_element.find('dt')
            dd_element = dl_element.find('dd')

            if dt_element and dd_element:
                key = dt_element['data-name']
                value = dd_element.text
                result_dict[key] = value
        result_dict['options'] = options if options else None
        result_dict['text'] = text if text else None
        print(result_dict)
        return json.dumps(result_dict)


app = FastAPI()


@app.post("/parse")
async def create_item(item: Item):
    item = await parse_apartment(item.url)
    return item


