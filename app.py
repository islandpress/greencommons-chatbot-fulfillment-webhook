# -*- coding:utf8 -*-
# !/usr/bin/env python
# Copyright 2017 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import print_function
from future.standard_library import install_aliases
install_aliases()

import urllib
import requests
import random
import json
import os

from flask import Flask
from flask import request
from flask import make_response

# Flask app should start in global layout
app = Flask(__name__)


@app.route('/webhook', methods=['POST'])
def webhook():
    req = request.get_json(silent=True, force=True)

    print("Request:")
    print(json.dumps(req, indent=4))

    func = request_dispatch(req)
    res = {
        "speech": 'This is dummy text.',
        "displayText": 'This is dummy text.',
        # "data": data,
        # "contextOut": [],
        "source": "greencommons-chatbot-fulfillment-webhook"
    }
    #res = handle_howmanyresources(req)
    if func:
        res = func(req)
    #res = processRequest(req)

    res = json.dumps(res, indent=4)
    # print(res)
    r = make_response(res)
    r.headers['Content-Type'] = 'application/json'
    return r


def request_dispatch(req):
    if req.get("result").get("action") == "how_many_resources_response":
        return handle_howmanyresources
    if req.get("result").get("action") == "show_me_response":
        return handle_showme
    if req.get("result").get("action") == "what_is_response":
        return handle_whatis
    return None


def get_all_resource_types():
    return ['articles','audio','books','courses','datasets','events','images',
            'posts','profiles','reports','slides','software','syllabi',
            'urls','videos']


def get_resource_type_singular_dict():
    return {'articles': 'article',
            'audios': 'audio file',
            'books': 'book',
            'courses': 'course',
            'datasets': 'dataset',
            'events': 'event',
            'images': 'image',
            'posts': 'post',
            'profiles': 'profile',
            'reports': 'report',
            'slides': 'slide',
            'software': 'software',
            'urls': 'url',
            'syllabi': 'syllabus',
            'videos': 'video'}


def handle_howmanyresources(req):
    q = req.get("result").get("parameters").get("eco-topics")
    if not q:
        return {}

    #resource_type = [req.get("result").get("parameters").get("resource_types")]
    all_resource_types = get_all_resource_types()

    resource_type = ','.join(all_resource_types)
    model_types = ['resources'] #, 'networks', 'lists']
    target_page = 1
    per_page = 1
    url = 'https://greencommons.net/api/v1/search?q={}' \
          '&filters[resource_types]={}' \
          '&filters[model_types]={}&page={}&per={}'.format(
            q, resource_type, ','.join(model_types), target_page, per_page)
    page = per = 0
    try:
        r = requests.get(url)
        if r.ok:
            j = r.json()
            last = j.get("links", {}).get("last")
            page = int(last.split("page=")[-1].split("&")[0])
            per = int(last.split("per=")[-1])
    except Exception as e:
        print(e)
    approx_total = page*per

    #approx_total = 1000

    speech = "Green Commons has {} resources on {}.".format(
        approx_total, q)
    return {
        "speech": speech,
        "displayText": speech,
        # "data": data,
        # "contextOut": [],
        "source": "greencommons-chatbot-fulfillment-webhook"
    }


def handle_showme(req):
    q = req.get("result").get("parameters").get("eco-topics")
    if not q:
        return {}

    resource_type = req.get("result").get("parameters").get("resource_types")
    if not resource_type or resource_type == "":
        resource_type = ','.join(get_all_resource_types())
    model_types = ['resources'] #, 'networks', 'lists']
    target_page = 1
    per_page = 10
    url = 'https://greencommons.net/api/v1/search?q={}' \
          '&filters[resource_types]={}' \
          '&filters[model_types]={}&page={}&per={}'.format(
            q, resource_type, ','.join(model_types),
            target_page, per_page)
    r = requests.get(url)
    data = None
    if r.ok:
        data = r.json().get("data")
    if not data:
        speech = "I couldn't find {} resources about {}.".format(resource_type, q)
    else:        
        d = random.choice(data).get("attributes")
        content = d.get("title", "")
        if d.get("short_content"):
            content += "\n" + d.get("short_content")
        if d.get("resource_url"):
            content += "\n" + d.get("resource_url")
        singular_resource_type = get_resource_type_singular_dict().get(
            resource_type, "resource")
        speech = "Checkout this {} about {}:\n{}".format(singular_resource_type,
                                                         q, content)
    return {
        "speech": speech,
        "displayText": speech,
        # "data": data,
        # "contextOut": [],
        "source": "greencommons-chatbot-fulfillment-webhook"
    }


def handle_whatis(req):
    # See: https://github.com/dbpedia/lookup
    q = req.get("result").get("parameters").get("eco-topics")
    if not q:
        return {}

    hits = 5
    url = "http://lookup.dbpedia.org/api/search/PrefixSearch?QueryClass=&MaxHits={}&QueryString={}".format(
        hits, urllib.request.quote(q))
    print(url)
    r = requests.get(url, headers={'Accept': 'application/json'})
    j = {}
    if r.ok:
        j = r.json()
    if j.get('results'):
        speech = ''
        print(j.get('results'))
        for res in j.get('results'):
            if res.get('description'):
                speech += res.get('description', '') + '\n'
            if res.get('uri'):
                speech += "|-> Learn more here: " + res.get('uri') + '\n\n'
        speech = speech.strip()
        print(speech)
    else:
        speech = "Sorry, I can't tell you anything about {}.".format(q)
    return {
        "speech": speech,
        "displayText": speech,
        # "data": data,
        # "contextOut": [],
        "source": "greencommons-chatbot-fulfillment-webhook"
    }


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))

    print("Starting app on port %d" % port)

    app.run(debug=False, port=port, host='0.0.0.0')
