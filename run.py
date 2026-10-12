"""Development entry point for the Grievance Portal."""

from grievance_app import create_app


app = create_app()


if __name__ == "__main__":
    app.run()
