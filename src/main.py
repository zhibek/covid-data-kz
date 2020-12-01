import requests
from bs4 import BeautifulSoup
import datetime
import pandas as pd

DEBUG = True
SOURCE_URL = 'https://www.coronavirus2020.kz/'
SOURCE_CSS_PATH = 'body > div.mainContainer > div.wrap_cov_cont ' \
    + '> div.first_cont_wrap:not(#manual_edit) > div.last_info_covid_bl > div.city_cov > div'
TARGET_PATHS = {
    'current_total': '../data/current_total.csv',
    'total_cases': '../data/total_cases.csv',
    'new_cases': '../data/new_cases.csv',
}
REGIONS = {
    'г. Нур-Султан': 'nursultan',
    'г. Алматы': 'almaty',
    'г. Шымкент': 'shyment',
    'Акмолинская область': 'akmola',
    'Актюбинская область': 'aktobe',
    'Алматинская область': 'almaty_region',
    'Атырауская область': 'atyrau',
    'Восточно-Казахстанская область': 'east_kazakhstan',
    'Жамбылская область': 'jambyl',
    'Западно-Казахстанская область': 'west_kazakhstan',
    'Карагандинская область': 'karagandy',
    'Костанайская область': 'kostanay',
    'Кызылординская область': 'kyzylorda',
    'Мангистауская область': 'mangistau',
    'Павлодарская область': 'pavlodar',
    'Северо-Казахстанская область': 'north_kazakhstan',
    'Туркестанская область': 'turkestan',
}
HEADERS = ['region_en']

print('Requesting data from "{}"'.format(SOURCE_URL))
result = requests.get(SOURCE_URL)
soup = BeautifulSoup(result.content, features='html.parser')
results = soup.select(SOURCE_CSS_PATH)

if len(results) != len(REGIONS):
    raise Exception('Invalid content: {}'.format(result.content.decode('utf-8')))

target_data = {}
for item in results:
    region_en = None
    region_ru = None
    total_cases = None
    new_cases = None

    for string in item.stripped_strings:
        if not region_en:
            region_total = string.split(' - ')
            if len(region_total) < 2:
                raise Exception('Unexpected content! {}'.format(item))

            region_ru = region_total[0]
            if region_ru not in REGIONS:
                raise Exception('Unexpected region! {}'.format(item))
            region_en = REGIONS[region_ru]
            total_cases = region_total[1]

    target_data[region_en] = {
        'region_en': region_en,
        'region_ru': region_ru,
        'total_cases': total_cases,
        'new_cases': new_cases,
    }

for target_type in TARGET_PATHS:
    target_path = TARGET_PATHS[target_type]

    df = pd.read_csv(target_path)

    date_today = datetime.datetime.today().strftime('%Y-%m-%d')

    if target_type == 'current_total':

        print('Processing "{}" - to check for updates!'.format(target_type))

        has_update = False
        date_today = 'current'

        for i, row in df.iterrows():
            region_en = row['region_en']
            item = target_data[region_en]
            today_value = item['total_cases']
            existing_value = row[date_today]
            df.loc[i, date_today] = today_value
            new_value = int(today_value) - int(existing_value)
            if new_value is None or new_value < 0:
                raise Exception('Unexpected value in "{}": "{}"'.format(region_en, new_value))
            target_data[region_en]['new_cases'] = new_value

            if int(existing_value) != int(today_value):
                has_update = True

        if DEBUG:
            print(target_data)

        if has_update:
            print('Updates found!')
        else:
            print('No updates found!')
            continue

    else:

        if has_update:
            print('Processing "{}" - updates found!'.format(target_type))
        else:
            continue

        df[date_today] = 0
        for i, row in df.iterrows():
            region_en = row['region_en']
            item = target_data[region_en]
            today_value = item[target_type]
            df.loc[i, date_today] = today_value

    df.to_csv(target_path, index=False)

print('Process complete!')
