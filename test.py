from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return "<h1>Flask Connected Successfully!</h1><p>Server is working.</p>"

if __name__ == "__main__":
    print("Starting Flask...")
    app.run(host="127.0.0.1", port=5000, debug=False)