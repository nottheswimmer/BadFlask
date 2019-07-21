from html import escape

from bad_flask import BadFlask

app = BadFlask()


@app.route(r'^/$')
def index(request):
    return 200, 'Hello world!'


@app.route(r'^/say_my_name$')
def say_my_name(request):
    name = request.query.get('name', None)
    if name:
        return 200, f'Hello, {escape(name)}!'
    else:
        return 400, 'You did not tell me your name!'


@app.route(r'/templated$')
def templated(request):
    name = request.query.get('name', 'stranger')
    return 200, app.render_template('base.html', name=name)


if __name__ == '__main__':
    app.run()
