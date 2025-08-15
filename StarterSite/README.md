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

---
## Portfolio Highlight

### Use Cases
*   **Rapid Project Kick-starter:** Provides a feature-rich foundation for any new Flask-based web application, saving days or weeks of setup time on common features like user accounts and an admin panel.
*   **CMS Development:** Can be extended into a lightweight, custom Content Management System (CMS) for blogs, portfolios, or small business websites.
*   **Internal Tools:** An excellent starting point for building internal dashboards and administrative tools for a company.
*   **Learning Flask:** A practical, working example for developers who want to learn how to structure and build a complete Flask application with common extensions.

### Proof of Concept
This project is a proof of concept for a **scalable and maintainable Flask application architecture**. It demonstrates:
*   **Modular Design:** The application is organized into logical modules (e.g., `views`, `auth`, `models`), promoting separation of concerns and making the codebase easier to manage and extend.
*   **Application Factory Pattern:** Uses the `create_app()` pattern, a best practice in Flask that facilitates testing and allows for multiple application instances with different configurations.
*   **Full-Featured Authentication:** A complete implementation of user registration, login, and session management using `Flask-Login`.
*   **Database Abstraction with an ORM:** Leverages `SQLAlchemy` to define database models and interact with the database, making the application portable across different database backends.
*   **Out-of-the-Box Admin Interface:** Integration of `Flask-Admin` to provide a secure, auto-generated administrative dashboard for managing application data.
*   **Containerization:** Includes a `Dockerfile` for easy containerization with Docker, demonstrating an understanding of modern deployment workflows.

### Hireable Skills
*   **Python & Flask:** Advanced proficiency in the Flask web framework, including blueprints, application factories, and extension management.
*   **Database Design & ORM:** Strong experience with `SQLAlchemy`, including defining models, managing relationships, and performing queries.
*   **User Authentication & Security:** Practical knowledge of implementing secure user authentication and session management (`Flask-Login`).
*   **Full-Stack Development:** Ability to build a complete web application from the database schema to the frontend templates.
*   **DevOps & Containerization:** Experience with Docker for creating portable and scalable application deployments.
*   **Software Architecture:** Expertise in designing clean, modular, and maintainable application structures.

---

## Tech Stack

-   **Backend**: Flask
-   **Database**: SQLAlchemy, SQLite
-   **Authentication**: Flask-Login
-   **Admin Interface**: Flask-Admin
-   **Rich Text Editing**: Flask-CKEditor
-   **Frontend**: HTML, Jinja2

## Visuals

*Coming Soon: A GIF showcasing the admin dashboard and the rich text editor.*

## Getting Started

These instructions will get you a copy of the project up and running on your local machine.

### Prerequisites

*   Python 3.8+

### Installation

1.  **Clone the repository:**
    ```sh
    git clone https://github.com/your-username/your-repository.git
    cd your-repository/StarterSite
    ```

2.  **Create a virtual environment and install dependencies:**
    ```sh
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    pip install -r requirements.txt
    ```

3.  **Run the application:**
    ```sh
    python webapp.py
    ```

4.  The application will start a development server and create the `DATABASE.db` file if it doesn't exist. It will be accessible at `http://127.0.0.1:5000`.

5.  **Admin Access:**
    You can log in with the default admin credentials to access the admin dashboard at `/admin`.
    -   **Username:** `D-Net`
    -   **Password:** `password`
