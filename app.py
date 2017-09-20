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

from urllib.parse import urlparse, urlencode
from urllib.request import urlopen, Request
from urllib.error import HTTPError

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
    res = handle_howmanyresources(req)
    # if func:
    #     res = func(req)
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
    return ['articles','books','reports','urls','audios',
            'courses','datasets','images','syllabuses',
            'videos','profiles']


def get_resource_type_singular_dict():
    return {'articles': 'article',
            'books': 'book',
            'reports': 'report',
            'urls': 'url',
            'audios': 'audio file',
            'courses': 'course',
            'datasets': 'dataset',
            'images': 'image',
            'syllabuses': 'syllabus',
            'videos': 'video',
            'profiles': 'profile'}


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
    url = 'https://greencommons.herokuapp.com/api/v1/search?q={}' \
          '&filters[resource_types]={}' \
          '&filters[model_types]={}&page={}&per={}'.format(
            q, resource_type, ','.join(model_types), target_page, per_page)
    r = requests.get(url)
    page = per = 0
    if r.ok:
        j = r.json()
        last = j.get("links", {}).get("last")
        page = int(last.split("page=")[-1].split("&")[0])
        per = int(last.split("per=")[-1])
    approx_total = page*per

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
    url = 'https://greencommons.herokuapp.com/api/v1/search?q={}' \
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
    q = req.get("result").get("parameters").get("eco-topics")
    if not q:
        return {}
    speech = "Right now I can't tell you anything about {}. "\
             "Ask me again once I've learned more.".format(q)
    return {
        "speech": speech,
        "displayText": speech,
        # "data": data,
        # "contextOut": [],
        "source": "greencommons-chatbot-fulfillment-webhook"
    }


def processRequest(req):
    if req.get("result").get("action") != "yahooWeatherForecast":
        return {}
    baseurl = "https://query.yahooapis.com/v1/public/yql?"
    yql_query = makeYqlQuery(req)
    if yql_query is None:
        return {}
    yql_url = baseurl + urlencode({'q': yql_query}) + "&format=json"
    result = urlopen(yql_url).read()
    data = json.loads(result)
    res = makeWebhookResult(data)
    return res


def makeYqlQuery(req):
    result = req.get("result")
    parameters = result.get("parameters")
    city = parameters.get("geo-city")
    if city is None:
        return None

    return "select * from weather.forecast where woeid in (select woeid from geo.places(1) where text='" + city + "')"


def makeWebhookResult(data):
    query = data.get('query')
    if query is None:
        return {}

    result = query.get('results')
    if result is None:
        return {}

    channel = result.get('channel')
    if channel is None:
        return {}

    item = channel.get('item')
    location = channel.get('location')
    units = channel.get('units')
    if (location is None) or (item is None) or (units is None):
        return {}

    condition = item.get('condition')
    if condition is None:
        return {}

    # print(json.dumps(item, indent=4))

    speech = "Right now in " + location.get('city') + ": " + condition.get('text') + \
             ", the temperature is " + condition.get('temp') + " " + units.get('temperature')

    print("Response:")
    print(speech)

    return {
        "speech": speech,
        "displayText": speech,
        # "data": data,
        # "contextOut": [],
        "source": "apiai-weather-webhook-sample"
    }


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))

    print("Starting app on port %d" % port)

    app.run(debug=False, port=port, host='0.0.0.0')
