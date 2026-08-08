from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return "Application successfully deployed and running on Vercel!"

if __name__ == "__main__":
    app.run(debug=True)
