import json
from random import randint


def random_question():
    with open('quotes.json') as fp:
        data = json.load(fp)
        random_index = randint(0, len(data)-1)
        return data[random_index]


print(random_question())
