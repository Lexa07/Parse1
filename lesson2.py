import requests
from bs4 import BeautifulSoup as bs
import pandas as pd


main_url = 'https://spb.hh.ru/'
page_link = '/search/vacancy'
headers = {"user-agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.64 Safari/537.36 Edg/101.0.1210.47"}
params = {'search_field': ['name', 'company_name', 'description']}
max_page = 20

params['text'] = input('Введите название вакансии: ')


def salary_extraction(vacancy_salary):
    salary_dict = {'min' : None, 'max' : None, 'cur' : None}

    if vacancy_salary:
        raw_salary = vacancy_salary.getText().split()
        if raw_salary[0] == 'до':
            salary_dict['max'] = int(raw_salary[1] + raw_salary[2])
        elif raw_salary[0] == 'от':
            salary_dict['min'] = int(raw_salary[1] + raw_salary[2])
        else:
            salary_dict['min'] = int(raw_salary[0] + raw_salary[1])
            salary_dict['max'] = int(raw_salary[3] + raw_salary[4])
        salary_dict['cur'] = raw_salary

    return salary_dict

vacancies = []
i = 0




while True:
    print(f'Page {i} начался процесс')
    response = requests.get(main_url + page_link, params=params, headers=headers)

    html = response.text
    soup = bs(html, 'html.parser')
    vacancies_soup = soup.find_all('div', {'class': 'vacancy-serp-item'})


    for vacancy in vacancies_soup :
        vacancy_base = {}
        vacancy_title = vacancy.find('a')
        vacancy_name = vacancy_title.getText()
        vacancy_link = vacancy_title['href'][: vacancy_title['href'].index('?')]
        vacancy_salary = salary_extraction(vacancy.find('span', {'data-qa': 'vacancy-serp__vacancy-compensation'}))
        vacancy_employer = vacancy.find('a', {'data-qa': 'vacancy-serp__vacancy-employer'}).getText().replace('\xa0', ' ')
        vacancy_address = vacancy.find('div', {'data-qa': 'vacancy-serp__vacancy-address'}).getText().replace('\xa0', ' ')

        vacancy_base['name'] = vacancy_name
        vacancy_base['link'] = vacancy_link
        vacancy_base['salary'] = vacancy_salary
        vacancy_base['employer'] = vacancy_employer
        vacancy_base['address'] = vacancy_address


        vacancies.append(vacancy_base)


    next_page = soup.find('a', {'data-qa': 'pager-next'})
    if not next_page or (i == max_page):
        break

    page_link = next_page['href']
    print(f'Page {i} закончился')
    i+=1


vacancies_data = pd.DataFrame(data=vacancies)
prefix = '_'.join(params['text'].split())
vacancies_data.to_csv(f'hh_vacancies_{prefix}.csv', index=False)








