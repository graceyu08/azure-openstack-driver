__author__ = 'graceyu'

import string
import random

def generate_random_name(length, prefix=None,
                         chars=string.ascii_lowercase+string.digits):
    string =  ''.join(random.choice(chars) for _ in range(length))
    if prefix:
        string = '-'.join((prefix, string))

    return string
