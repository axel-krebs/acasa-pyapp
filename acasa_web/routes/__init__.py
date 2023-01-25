# routes
import os

file_path = os.path.realpath(__file__)
API_FILE = "{}/api.json".format(file_path)

from openapi import load

with open(API_FILE) as json_file:
    swagger = load(json_file)
    # Do sth. with it..