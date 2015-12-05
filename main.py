import json
import os.path
import re

from bson import ObjectId
from flask import Flask, render_template, send_from_directory
from pymongo import MongoClient
from uwaterlooapi import UWaterlooAPI

with open('key.json') as f:
    key = json.load(f)['key']

uw = UWaterlooAPI(api_key=key)

course_code_r = re.compile(r"([A-Z]+)([0-9]+)")

client = MongoClient('localhost', 27017)
collection = client.courses.prereqs

app = Flask(__name__)

DEBUG = False

class Encoder(json.JSONEncoder):
  def default(self, obj):
    if isinstance(obj, ObjectId):
      return str(obj)
    else:
      return obj

def construct_json(course_code):
  """Intermediate node has form:
  {
    "course_code": str,
    "title": str,
    "prerequisite_groups": [
      {
        "prerequisites": [
          Node,
          Node,
          ...
        ]
      },
      {
        "prerequisites": [
          Node,
          Node,
          ...
        ]
      },
      ...
    ]
  }

  Leaf node has form:
  {
    "course_code": str,
    "title": str
  }
  """
  in_db = collection.find_one({"course_code": course_code})
  if in_db:
    return in_db


  (subject, catalog_no) = course_code_r.match(course_code).groups()
  course_details = uw.course(subject, catalog_no)
  course_prereqs = uw.course_prerequistes(subject, catalog_no)

  data = {
    "course_code": course_code,
    "title": course_details.get("title")
  }

  prereq_group_list = course_prereqs.get("prerequisites_parsed")
  if DEBUG:
    print(course_code)
    print "\t" + str(prereq_group_list)
  if (prereq_group_list):
    data["prerequisite_groups"] = []
    for prereq_group in prereq_group_list:
      if type(prereq_group) is str or type(prereq_group) is unicode or type(prereq_group) is int:
        continue
      else:
        prereq_group_data = {
          "prerequisites": []
        }
        for prereq in prereq_group:
          if type(prereq) is int:
            continue
          elif type(prereq) is list:
            for p in prereq:
              if type(p) is int:
                continue
              prereq_group_data["prerequisites"].append(construct_json(p))
          else:
            prereq_group_data["prerequisites"].append(construct_json(prereq))
        data["prerequisite_groups"].append(prereq_group_data)
  else:
    pass
  collection.insert_one(data)
  return data


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

  filename = "json/%s.json" % course_code

  if os.path.isfile(filename):
    pass
  else:
    data = construct_json(course_code)
    with open(filename, "w") as the_file:
      json.dump(data, the_file, cls=Encoder)

@app.route("/graph/<course_code>")
def do_it(course_code):
  course_code = course_code.upper()
  if course_code_r.match(course_code):
    prereq_graph(course_code)
    return render_template('template.html', course_code=course_code)
  else:
    return None

@app.route("/json/<path:path>")
def send_json(path):
  return send_from_directory("json", path)

if __name__ == "__main__":
  app.debug = DEBUG
  app.run()