from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return '''
    <html>
        <head>
            <title>Habit Tracker</title>
        </head>
        <body style="font-family: Arial; text-align: center; padding: 50px;">
            <h1>🎯 Habit Tracker Live</h1>
            <p>Your journey to better habits starts here!</p>
        </body>
    </html>
    '''

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
    