from pedafiche.web import create_app

application = app = create_app()

if __name__ == "__main__":
    app.run(debug=False, host="127.0.0.1", port=5050)
