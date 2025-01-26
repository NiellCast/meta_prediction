# test_main.py

from flask import Flask

app = Flask(__name__)

@app.before_request
def initialize():
    print("Inicialização antes de cada pedido.")

@app.route('/')
def index():
    return "Hello, World!"

if __name__ == "__main__":
    app.run(debug=True)
