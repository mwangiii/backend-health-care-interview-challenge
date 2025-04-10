"""This is the main entry point for the application."""
from app import create_app
from config import Config

app = create_app()
print(Config.JWT_TOKEN_LOCATION)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
