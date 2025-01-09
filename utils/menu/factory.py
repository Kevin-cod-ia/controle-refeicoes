import pprint
from random import randint
from faker import Faker
def rand_ratio():
    return randint(840, 900), randint(473, 573)
fake = Faker('pt_BR')

def make_week_menu():
    return {
        'id': fake.random_number(digits=2, fix_len=True),
        'initial_date_period': (fake.day_of_month() + '/' + fake.month()),
        'final_date_period': (fake.day_of_month() + '/' +  fake.month()),
        'date_meal': (fake.day_of_month() + '/' +  fake.month()),
        'image_meal': 
            {
                'url': 'https://loremflickr.com/%s/%s/food,cook' % rand_ratio(),
            },
        'title': fake.sentence(nb_words=2),
        'side_dish': fake.sentence(nb_words=3),
        'options': {
            'id_option_1': fake.random_number(digits=2, fix_len=True),
            'name_option_1': 'Omelete',
            'id_option_2': fake.random_number(digits=2, fix_len=True),
            'name_option_2': 'Marmita de Frango',
            'id_option_3': fake.random_number(digits=2, fix_len=True),
            'name_option_3': 'Marmita de Carne',
        },
        'created_at': fake.date_time(),
        
    }