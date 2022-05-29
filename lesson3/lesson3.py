import logging
from pprint import pprint
from time import sleep
from typing import Optional

import requests
from bs4 import BeautifulSoup as bs
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.errors import DuplicateKeyError
from bson.objectid import ObjectId

from constants import *

logging.basicConfig(format='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger('job_scraper')
logger.setLevel(logging.INFO)


def get_response(url, headers, params=None):
    timeouts = (5, 5)

    for i in range(5):
        response = requests.get(url,
                                headers=headers,
                                params=params,
                                timeout=timeouts)
        if response.ok:
            logger.debug('response - OK')
            break
        else:
            logger.debug('response - NOT OK (%s)', response.status_code)
            sleep_time = i + 1
            logger.warning(f'Не смог получить ответ для %s. Подождем %d сек.',
                           response.url,
                           sleep_time)
            sleep(sleep_time)
    else:
        raise SystemExit(1, f'Так и не смог получить ответ для {response.url}')

    # на случай редиректа hh.ru -> rostov.hh.ru
    splitted_response_url = response.url.split('/')
    new_main_url = f'{splitted_response_url[0]}//{splitted_response_url[2]}'
    return response, new_main_url


def get_int(re_match):
    return int(re_match.group().replace(' ', ''))


def get_salary(tag):
    if tag is None:
        return Salary(None, None, None)

    text = clear_tag_text(tag)
    # получалось неплохо через всякие сплиты/слайсы/джоины,
    # но потом пришли 'бел. руб.' и все сломалось =)
    # поэтому регулярки
    if 'от' in text:
        re_salary = RE_SALARY.search(text)
        salary = get_int(re_salary)
        re_currency = RE_CURRENCY.search(text, re_salary.end())
        return Salary(salary, None, re_currency.group())
    elif 'до' in text:
        re_salary = RE_SALARY.search(text)
        salary = get_int(re_salary)
        re_currency = RE_CURRENCY.search(text, re_salary.end())
        return Salary(None, salary, re_currency.group())
    else:
        re_min_salary = RE_SALARY.search(text)
        min_salary = get_int(re_min_salary)
        re_max_salary = RE_SALARY.search(text, re_min_salary.end())
        max_salary = get_int(re_max_salary)
        re_currency = RE_CURRENCY.search(text, re_max_salary.end())
        return Salary(min_salary, max_salary, re_currency.group())


def clear_tag_text(tag):
    text = tag.getText()
    text = text.replace('\n', '')
    splitted = [word for word in text.split() if word]
    text = ' '.join(splitted)
    return text


def parse_vacancy_link(tag):
    link = tag.get('href')
    return f'{MAIN_URL}{link}'


def save_to_file(data, file_name):
    with open(file_name, 'w', encoding='utf8') as f:
        f.write(data)


def parse_response(response, main_url):
    vacancies_info = []

    soup = bs(response.text, 'html.parser')
    anchor = soup.find('div', {'class': 'vacancy-serp-content'})

    vacancy_results = anchor.find('div', {'data-qa': 'vacancy-serp__results'})
    vacancies = vacancy_results.find_all('div', {'class': 'vacancy-serp-item'})
    logger.info('Нашел %d вакансий. Обрабатываю...', len(vacancies))
    for vacancy in vacancies:
        title_tag = vacancy.find('a', {'data-qa': 'vacancy-serp__vacancy-title'})
        salary_tag = vacancy.find('span', {'data-qa': 'vacancy-serp__vacancy-compensation'})

        vacancy_info = {
            'name': clear_tag_text(title_tag),
            'salary': get_salary(salary_tag),
            'link': title_tag.get('href'),
            'site': main_url,
        }
        vacancies_info.append(vacancy_info)

    return vacancies_info, anchor


def get_mongo_collection(collection_name: str) -> Optional[Collection]:
    client = MongoClient(host=MONGODB_HOST,
                         port=MONGODB_PORT,
                         username='gb_mongo_root',
                         password='gb_mongo_root_pass')
    db = client[MONGODB_DB_NAME]

    collection = getattr(db, collection_name, None)
    if collection is None:
        raise ValueError(1, f"Коллекция {collection_name} не найдена")

    return collection


def save_to_mongo(data):
    hh_vacancies = get_mongo_collection('hh_vacancies')
    for row in data:
        try:
            vacancy_id = row['link'].split('/')[4].split('?')[0]
            _id = ObjectId(f'{vacancy_id:0>24}')
            hh_vacancies.insert_one({'_id': _id, **row})
        except DuplicateKeyError as e:
            logger.debug('Для ID=%s уже в базе.', vacancy_id)
            pass


def filter_vacancies_by_salary(salary_value):
    sleep(2)
    print(f'--- Вакансии с ЗП {salary_value:,}+')
    hh_vacancies = get_mongo_collection('hh_vacancies')
    for row in hh_vacancies.find({
        '$or': [{'salary': {'$elemMatch': {'$gte': salary_value}}}]
    }):
        pprint(row)


def main():
    page_cnt = 1
    url = 'https://spb.hh.ru/vacancies/inzhener'
    headers = {"user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.64 Safari/537.36 Edg/101.0.1210.47"}
    params = {'search_field': ['name', 'company_name', 'description']}


    while True:
        logger.info('Parse page #%d', page_cnt)
        response, main_url = get_response(url, headers=headers, params=params)
        if not response:
            logger.error('NO response from %s', url)
            raise SystemExit(1)

        try:
            vacancies_info, anchor = parse_response(response, main_url)
        except ValueError as e:
            logger.exception(e)
            save_to_file(response.text, 'error_response.html')
            raise SystemExit(1)

        logger.info('Сохраняю их в Mongo')
        save_to_mongo(vacancies_info)

        logger.info('Ищу следующую страницу...')
        next_link = anchor.find('a', {'data-qa': 'pager-next'})
        if next_link:
            logger.info('Нашел.')
            url = f'{main_url}{next_link.get("href")}'
            params = None
            page_cnt += 1
            sleep(1)  # не будем спамить запросами
        else:
            logger.info('Всего обработано %d страниц', page_cnt)
            break

    filter_vacancies_by_salary(100_000)


if __name__ == '__main__':
    logger.info('--- START')
    main()
    logger.info('--- END')
