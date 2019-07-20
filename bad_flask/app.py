import re
import os
from http import HTTPStatus
from urllib.parse import parse_qs
from . import template

HTTP_STATUSES = {s.value: f'{s.value} {s.phrase}' for s in HTTPStatus}


class WSGIRequest:
    """
    Abstraction layer for the raw environ, like the Django Request object.
    """

    def __init__(self, environ):
        self.environ = environ
        self.method = environ.get('REQUEST_METHOD', None)
        self.path_info = environ.get('PATH_INFO', None)
        self.query = {key: value[-1] for key, value in parse_qs(environ.get('QUERY_STRING', '')).items()}


class SimpleRule:
    """
    Heavily stupified version of Werkzeug's Routing Rules.
    """

    def __init__(self, url_pattern, endpoint):
        self.url_pattern = re.compile(url_pattern)
        self.endpoint = endpoint


class BadFlask:
    def __init__(self, **options):
        self.url_rules = []
        self.view_functions = {}
        self.template_folder = options.get('template_folder', 'templates')

    def __call__(self, environ, start_response):
        request = WSGIRequest(environ)
        headers = [('Content-type', 'text/html; charset=utf-8')]

        view_func = None
        for rule in self.url_rules:
            if rule.url_pattern.match(request.path_info):
                view_func = self.view_functions[rule.endpoint]
                break

        if view_func is None:
            view_func = self.error_404

        status, body = view_func(request)
        start_response(HTTP_STATUSES[status], headers)

        if isinstance(body, str):
            body = body.encode()

        yield body

    def route(self, rule, **options):
        """
        Flask-like routing.
        """

        def decorator(f):
            endpoint = options.pop("endpoint", None)
            self.add_url_rule(rule, endpoint, f, **options)
            return f

        return decorator

    @staticmethod
    def error_404(*args, **kwargs):
        return 404, 'Page Not Found'

    def add_url_rule(
            self, url_pattern, endpoint=None, view_func=None, **options):

        if endpoint is None:
            assert view_func is not None, "expected view func if endpoint is not provided."
            endpoint = view_func.__name__

        self.url_rules.append(SimpleRule(url_pattern, endpoint))
        self.view_functions[endpoint] = view_func

    def run(self, host='127.0.0.1', port=8000):
        from wsgiref.simple_server import make_server
        with make_server(host, port, self) as httpd:
            print(f"Running debug server at http://{host}:{port}...")
            httpd.serve_forever()

    def render_template(self, template_name, **context):
        with open(os.path.join(self.template_folder, template_name), 'r') as f:
            unrendered_template = f.read()
        return template.render(unrendered_template, context)
