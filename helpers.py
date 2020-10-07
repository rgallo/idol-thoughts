from __future__ import division
from __future__ import print_function

from functools import reduce
import requests


class StlatTerm:
    def __init__(self, a, b, c):
        self.a = a
        self.b = b
        self.c = c

    def calc(self, val):
        return self.a * ((self.b + val) ** self.c)


def geomean(numbers):
    correction = .001 if 0.0 in numbers else 0.0
    return (reduce(lambda x, y: x*y, [(n + correction) for n in numbers])**(1.0/len(numbers))) - correction


TERM_RESULTS = {}


def load_terms(term_url, special_cases=None):
    special_case_list = [case.lower() for case in special_cases] if special_cases else []
    if term_url not in TERM_RESULTS:
        results, special = {}, {}
        data = requests.get(term_url).text
        splitdata = [d.split(",") for d in data.split("\n")[1:] if d]
        for row in splitdata:
            name = row[0].lower()
            if name in special_case_list:
                special[name] = row[1:]
            else:
                results[name] = StlatTerm(float(row[1]), float(row[2]), float(row[3]))
        TERM_RESULTS[term_url] = (results, special)
    return TERM_RESULTS[term_url]

