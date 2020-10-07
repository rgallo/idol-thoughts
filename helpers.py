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


def load_terms(term_url):
    if term_url not in TERM_RESULTS:
        data = requests.get(term_url).text
        splitdata = [d.split(",") for d in data.split("\n")[1:] if d]
        terms = {name.lower(): StlatTerm(a, b, c) for name, a, b, c in splitdata}
        TERM_RESULTS[term_url] = terms
    return TERM_RESULTS[term_url]

