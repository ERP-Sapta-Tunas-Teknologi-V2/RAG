from flask import Flask, send_from_directory, jsonify

from extensions import limiter
from routes.chat import chat_bp

def create_app():
    app = Flask(__name__)

    limiter.init_app(app)
    app.register_blueprint(chat_bp, url_prefix="/api")

    @app.route("/")
    def index():
        return send_from_directory("static", "index.html")

    @app.errorhandler(429)
    def ratelimit_handler(e):
        return jsonify({"error": "rate limit exceeded"}), 429

    return app

app = create_app()

if __name__ == "__main__":
    app.run(
        debug=True,
        host="0.0.0.0",
        port=5000,
    )