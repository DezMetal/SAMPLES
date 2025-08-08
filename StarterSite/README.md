# StarterSite - Flask Web Application Boilerplate

StarterSite is a boilerplate project for building web applications with Python and the Flask framework. It comes with a variety of common features pre-configured, providing a solid foundation to accelerate development.

The project is structured with separate modules for authentication (`auth.py`), views (`views.py`), and database models (`models.py`), promoting a clean and organized codebase.

## Included Features

-   **User Authentication**: A complete user registration and login system is implemented using `Flask-Login`. It includes routes for logging in, registering, and logging out.
-   **Admin Dashboard**: An admin interface is pre-configured using `Flask-Admin`, providing a simple way to manage database models (Users, Pages, Sessions) through a web UI.
-   **Database Integration**: The application is set up to use `SQLAlchemy` as its ORM for database interaction. It includes pre-built models for `User`, `Page`, and `Session`.
-   **Database Creation & Seeding**: The application automatically creates the SQLite database file (`DATABASE.db`) on first run and seeds it with an initial admin user and a sample page.
-   **Rich Text Editing**: The `Flask-CKEditor` extension is integrated, providing a powerful WYSIWYG editor for creating and editing content.
-   **Structured Layout**: The project uses a base layout template (`base_layout.html`) with separate files for the navigation bar (`nav.html`) and footer (`footer.html`), making it easy to maintain a consistent look and feel across the site.
-   **File Uploads**: The application is configured to handle file uploads, with a designated `UPLOAD_FOLDER`.

## How to Use

1.  Install the dependencies listed in `requirements.txt`.
2.  Run the `webapp.py` script.
3.  The application will start a development server, create the database if it doesn't exist, and be accessible in your browser.
4.  You can log in with the default admin credentials (`uname`: 'D-Net', `passwd`: 'password') to access the admin dashboard at `/admin`.
