import json

from uwaterlooapi import UWaterlooAPI

with open('key.json') as f:
    key = json.load(f)['key']

uw = UWaterlooAPI(api_key=key)

def prereq_graph(course_code):
  """Produce `course_code`.json containing data for visualization.

  Prerequisites of a course are represented as the corresponding
  node's children.

  Args:
    str(course_code): The root course code, e.g. "MATH239".
  Ensures:
    `course_code`.json exists and is valid.
  Returns:
    Nothing.
  """