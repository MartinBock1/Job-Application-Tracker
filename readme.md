Of course! Adding a reference to the frontend is an excellent idea to make the project documentation complete.

Here is your updated `README.md` file with a new section for the frontend, placed right after the introduction for high visibility.

---

# 🚀 Job Application Tracker API
DjangoPythonLicenseAPI Docs

This is the backend for the Job Application Tracker, a robust API built with Django and the Django REST Framework. It serves as the central interface for managing job applications, companies, contacts, and notes.

## 🌐 Frontend Application
The official frontend for this API is a modern single-page application built with Angular. You can find the complete project and setup instructions in its dedicated repository:

*   **Frontend Repository**: [https://github.com/MartinBock1/application-tracker-fe](https://github.com/MartinBock1/application-tracker-fe)

To clone the frontend project, use the following command:
```bash
git clone https://github.com/MartinBock1/application-tracker-fe.git
```

## ✨ Key Features
*   **Token-based Authentication**: Secure user registration and login (email/password) using DRF's built-in Token Authentication.
*   **Comprehensive CRUD Operations**: Full management of:
    *   Applications
    *   Companies
    *   Contacts
    *   Notes
*   **Data Isolation**: Users can only access and manipulate their own data. All API endpoints are automatically filtered by the currently authenticated user.
*   **📦 Data Backup & Restore**: Command-line tools to easily export all user data (applications, companies, etc.) to a single JSON file and import it back. Perfect for backups or migrating your data.
*   **Smart Nested Data Handling**: Notes can be created, updated, or deleted directly when updating an application in a single request.
*   **Auto-Generated API Documentation**: Thanks to `drf-spectacular`, interactive Swagger UI and ReDoc documentation are generated automatically.
*   **Admin Interface**: A full-featured Django Admin panel for easy data management and review.

## 📚 API Documentation
The API documentation is generated automatically and is the best way to explore all available endpoints and their schemas. After starting the server, the documentation is available at the following URLs:

*   **Swagger UI**: `http://127.0.0.1:8000/api/docs/`
*   **ReDoc**: `http://127.0.0.1:8000/api/redoc/`
*   **Schema File**: `http://127.0.0.1:8000/api/schema/`

## 🛠️ Tech Stack
*   **Backend**: Django, Django REST Framework
*   **Database**: SQLite3 (for development), easily switchable to PostgreSQL for production.
*   **API Documentation**: `drf-spectacular`
*   **CORS Handling**: `django-cors-headers`

## ⚙️ Setup & Installation
Follow these steps to set up and run the project locally.

#### 1. Prerequisites
*   Python 3.10+
*   Git

#### 2. Clone the Project
```bash
git clone <REPOSITORY-LINK>
cd <projectfolder>
```

#### 3. Create and Activate a Virtual Environment
It is highly recommended to use a virtual environment.

```bash
# Create the virtual environment
python -m venv env

# Activate on Windows
.\env\Scripts\activate

# Activate on macOS/Linux
source env/bin/activate
```

#### 4. Install Dependencies
```bash
# Install all packages from the requirements file
pip install -r requirements.txt
```

#### 5. Migrate the Database
This command creates the necessary database tables based on the project's models.
```bash
python manage.py migrate
```

#### 6. Create a Superuser
A superuser is required to access the Django Admin panel.
```bash
python manage.py createsuperuser
```
Follow the prompts to set a username, email, and password.

#### 7. Start the Development Server
```bash
python manage.py runserver
```
The backend is now running and accessible at `http://127.0.0.1:8000`.

## 📦 Data Management Commands
This project includes two powerful management commands to handle data backup and restoration.

### Exporting All Data
The `export_data` command gathers all data from the `Company`, `Contact`, `Application`, and `Note` models and saves it into a single, structured JSON file.

*   **Usage**:
    ```bash
    # Export to the default file (full_export.json)
    python manage.py export_data

    # Export to a custom file
    python manage.py export_data --filename my_backup.json
    ```

### Importing Data
The `import_data` command reads a JSON file created by `export_data` and populates the database with its content. It intelligently uses an **"update or create"** logic: if an item with the same ID already exists, it will be updated; otherwise, it will be created. This prevents duplicates and makes the process safe to run.

*   **Usage**:
    ```bash
    # Before running, ensure the target database is migrated.
    python manage.py migrate

    # Import from the default file (full_export.json)
    python manage.py import_data

    # Import from a custom file
    python manage.py import_data --filename my_backup.json
    ```

## 🗺️ API Endpoints Overview
All endpoints require Token Authentication, except for those under `/api/auth/`.

| Resource     | URL Prefix          | Supported Methods                  |
|--------------|---------------------|------------------------------------|
| **Auth**     | `/api/auth/`        | `POST` (/registration/, /login/)   |
| **Companies**| `/api/companies/`   | `GET`, `POST`, `PUT`, `PATCH`, `DELETE` |
| **Contacts** | `/api/contacts/`    | `GET`, `POST`, `PUT`, `PATCH`, `DELETE` |
| **Applications**| `/api/applications/`| `GET`, `POST`, `PUT`, `PATCH`, `DELETE` |
| **Notes**    | `/api/notes/`       | `GET`, `POST`, `PUT`, `PATCH`, `DELETE` |


## 📜 License
This project is licensed under the MIT License. See the `LICENSE` file for more details.
