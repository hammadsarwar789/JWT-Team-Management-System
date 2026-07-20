from dotenv import load_dotenv

load_dotenv()  # reads .env into environment variables before Config is used

from app import create_app  # noqa: E402

app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=5000)
