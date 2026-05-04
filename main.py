from app import app
from auth import router as auth_routes
from routes import (
    public_routes,
    dashboard_routes,
    presentations_routes,
    objectives_routes,
    questions_routes,
    sessions_routes,
    participant_routes,
    api_routes
)

# Register all blueprints
app.register_blueprint(auth_routes)
app.register_blueprint(public_routes)
app.register_blueprint(dashboard_routes)
app.register_blueprint(presentations_routes)
app.register_blueprint(objectives_routes)
app.register_blueprint(questions_routes)
app.register_blueprint(sessions_routes)
app.register_blueprint(participant_routes)
app.register_blueprint(api_routes, url_prefix='/api')

# TODO: remove debug=True in production
if __name__ == "__main__":
    app.run(debug=True, port=5000)