#!/usr/bin/env python3

from pprint import pprint

import json
import random
import base64
from html import escape as html_escape

from collections import deque
from urllib.parse import parse_qs

max_nr_messages = 25

html = """<!DOCTYPE html>
    <head>
        <meta charset="utf-8">
        <meta http-equiv="X-UA-Compatible" content="IE=edge,chrome=1">
        <title>Message Board</title>
        <meta name="description" content="A simple message board written in python">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
        body {{
            margin: 10px auto;
            max-width: 650px;
            line-height: 1.6;
            font-size: 18px;
            color: #444;
            padding: 0 10px
        }}

        h1,h2,h3 {{
            line-height: 1.2
        }}

        hr {{
            display: block;
            height: 1px;
            border: 0;
            border-top: 1px solid #ccc;
            margin: 1em 0;
            padding: 0;
        }}
        </style>
    </head>
    <body>
        <h1>Message Board</h1>
        <p>Last {msg_count} messages left here</p>

        {content}

        <form action="/submit" method="post">
          Add a message:&nbsp
          <input type="text" name="message" value="" required autofocus>
          <input type="submit" value="Submit">
        </form>
        <hr>
    </body>
</html>
"""

default = [
    "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. P Quis lectus nulla at volutpat diam ut venenatis tellus in.",
    "Porttitor massa id neque aliquam vestibulum morbi blandit cursus. Aliquet risus feugiat in ante metus dictum at tempor commodo. Fermentum odio eu feugiat pretium nibh ipsum.",
    "Curabitur gravida arcu ac tortor dignissim convallis aenean et. Neque vitae tempus quam pellentesque. Non diam phasellus vestibulum lorem sed risus. Tortor id aliquet lectus proin nibh nisl condimentum.",
    "Accumsan tortor posuere ac ut consequat semper viverra nam libero. Leo duis ut diam quam nulla porttitor"
]

default = ["Example entry #{}: {}".format(i, x) for i, x in enumerate(default)]

messages = deque(default, maxlen=max_nr_messages)

def application(env, start_response):

    if env["REQUEST_METHOD"] == "POST":

        try:
            l = int(env.get('CONTENT_LENGTH', 0))
        except KeyError:
            start_response('411 Length Required', [('Content-Type', 'application/json')])
            return [json.dumps({"error":{"code":411, "message": "Content-Length header missing"}}).encode()]
        if l > 150:
            start_response('413 Payload Too Large', [('Content-Type', 'application/json')])
            return [json.dumps({"error":{"code":413, "message": "Payload Too Large"}}).encode()]

        message = env['wsgi.input'].read(l).decode()
        if not message:
            start_response('400 Bad Request', [('Content-Type', 'application/json')])
            return [json.dumps({"error":{"code":400, "message": "message not provided"}}).encode()]
        try:
            message = json.loads(message)["message"]
        except json.decoder.JSONDecodeError:
            pass
        except KeyError:
            start_response('400 Bad Request', [('Content-Type', 'application/json')])
            return [json.dumps({"error":{"code":400, "message": "message key missing from json payload data"}}).encode()]

        if message.startswith("message="):
            message = parse_qs(message)["message"][0]

        messages.appendleft(html_escape(message.strip()))
        #start_response("200 OK", [('Content-Type', 'application/json')])

    if env["PATH_INFO"] == "/submit":
        start_response("303 See Other", [('Content-Type', 'application/json'),
                                         ('Location', '/')])
        return [b"OK"]

    if env["PATH_INFO"] == "/clear":
        messages.clear()
        messages.extendleft(default)
        start_response("303 See Other", [('Content-Type', 'application/json'),
                                         ('Location', '/')])
        return [b"OK"]

    if env["PATH_INFO"] == "/json" or 'HTTP_USER_AGENT' in env and env['HTTP_USER_AGENT'].startswith(('python-requests', 'HTTPie', 'curl', 'Wget')):
        start_response("200 OK", [('Content-Type', 'application/json')])
        return [json.dumps(list(messages), indent=4).encode()]


    start_response('200 OK', [('Content-Type', 'text/html')])
    content = []
    for message in list(messages):
        content.append("          <li>{}</li>\n".format(message))
    content = "<ol>\n{}        </ol>".format("".join(content))
    return [html.format(msg_count=len(messages), content=content).encode()]


if __name__ == "__main__":
    from wsgiref.simple_server import make_server

    httpd = make_server('0.0.0.0', 8080, application)
    print("Serving on http://0.0.0.0:8080/")
    httpd.serve_forever()
