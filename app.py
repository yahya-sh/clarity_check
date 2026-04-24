from flask_wtf.csrf import CSRFProtect
from flask import Flask, render_template
import os

app = Flask(__name__)
csrf = CSRFProtect(app)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'insecure-bc054a63d0f9c2b537d4b0f6bebadb3630dd73495a140241')

@app.route('/')
def index():
    return render_template('index.html')


# TODO: remove debug=True in production
if __name__ == "__main__":
    app.run(debug=True)