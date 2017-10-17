import urllib
import httpbin
from flask import session, redirect, url_for, escape, request, render_template, make_response

from requestbin import app, db

def update_recent_bins(name):
    if 'recent' not in session:
        session['recent'] = []
    if name in session['recent']:
        session['recent'].remove(name)
    session['recent'].insert(0, name)
    if len(session['recent']) > 10:
        session['recent'] = session['recent'][:10]
    session.modified = True


def expand_recent_bins():
    if 'recent' not in session:
        session['recent'] = []
    recent = []
    for name in session['recent']:
        try:
            recent.append(db.lookup_bin(name))
        except KeyError:
            session['recent'].remove(name)
            session.modified = True
    return recent


def full_endpoint_api(return_dict=False):
    """
    return json response accord http method using httpbin
    """
    FOR_GET = ('url', 'args', 'headers', 'origin')
    FOR_NONE_GET = ('url', 'args', 'form', 'data', 'origin', 'headers', 'files', 'json')
    method_v = {
        'GET': FOR_GET,
        'HEAD': FOR_GET,
        "POST": FOR_NONE_GET,
        "PUT": FOR_NONE_GET,
        "PATCH": FOR_NONE_GET,
        "DELETE": FOR_NONE_GET,
    }

    if request.method not in method_v:
        return httpbin.status_code(405)

    dict_value = {
        "code" 0,
        "msg": "ok",
        "data": httpbin.get_dict(*method_v[request.method])
    }

    if return_dict:
        return dict_value
    return httpbin.jsonify(dict_value)


@app.endpoint('views.home')
def home():
    return render_template('home.html', recent=expand_recent_bins())


@app.endpoint('views.bin')
def bin(name):
    try:
        bin = db.lookup_bin(name)
    except KeyError:
        return "Not found\n", 404
    if request.query_string == 'inspect':
        if bin.private and session.get(bin.name) != bin.secret_key:
            return "Private bin\n", 403
        update_recent_bins(name)
        return render_template('bin.html',
            bin=bin,
            base_url=request.scheme+'://'+request.host)
    else:
        db.create_request(bin, request)
        resp = full_endpoint_api()
        resp.headers['Sponsored-By'] = "https://www.runscope.com"
        return resp


@app.endpoint('views.docs')
def docs(name):
    doc = db.lookup_doc(name)
    if doc:
        return render_template('doc.html',
                content=doc['content'],
                title=doc['title'],
                recent=expand_recent_bins())
    else:
        return "Not found", 404
