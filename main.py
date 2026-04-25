from app import app
from routes.auth import auth as auth_routes
from routes.instructor import instructor as instructor_routes
from routes.main import main as main_routes

app.register_blueprint(auth_routes)
app.register_blueprint(instructor_routes)
app.register_blueprint(main_routes)

# TODO: remove debug=True in production
if __name__ == "__main__":
    app.run(debug=True)