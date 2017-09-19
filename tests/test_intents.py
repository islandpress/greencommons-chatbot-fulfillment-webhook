import json
import sys
import glob
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import app


def get_example_handlerfunc_dict():
    return {"example_default_fallback_intent.json": None,
            "example_default_welcome_intent.json": None,
            "example_help_intent.json": None,
            "example_how_many_resources_intent.json": app.handle_howmanyresources,
            "example_showme_intent_books.json": app.handle_showme,
            "example_showme_intent_videos.json": app.handle_showme,
            "example_whatis_intent.json": app.handle_whatis}


def test_handler():
    intent_handlerfunc_dict = get_example_handlerfunc_dict()
    for fn in glob.glob('../vectors/example*json'):
        with open(fn) as fp:
            d = json.load(fp)
        func = app.request_dispatch(d)
        base_fn = os.path.basename(fn)
        assert intent_handlerfunc_dict[base_fn] == func


def test_how_many_resources_intent():
    """Note: this is an integration test!"""
    with open("../vectors/example_how_many_resources_intent.json") as fp:
        d = json.load(fp)
    res = app.handle_howmanyresources(d)
    print(res)
    assert res


def test_showme_intent_books():
    """Note: this is an integration test!"""
    with open("../vectors/example_showme_intent_books.json") as fp:
        d = json.load(fp)
    res = app.handle_showme(d)
    print(res)
    assert res


def test_showme_intent_videos():
    """Note: this is an integration test!"""
    with open("../vectors/example_showme_intent_videos.json") as fp:
        d = json.load(fp)
    res = app.handle_showme(d)
    print(res)
    assert res


def test_whatis_intent():
    """Note: this is an integration test!"""
    with open("../vectors/example_whatis_intent.json") as fp:
        d = json.load(fp)
    res = app.handle_whatis(d)
    print(res)
    assert res
