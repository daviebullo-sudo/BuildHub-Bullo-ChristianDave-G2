# BuildHub

Web-based renovation project management for homeowners and small contractors.
Phase 1 (Project Development 1): **Account Feature** — registration, login/logout,
role-based dashboards (Homeowner / Contractor), and user profile.

**Stack:** Django (templates for the frontend) + PostgreSQL / Supabase.

## Quick start (development, no PostgreSQL needed)

The included `.env` has `USE_SQLITE=True`, so you can run the app right away:

```bash
python -m venv venv
venv\Scripts\activate          # macOS / Linux: source venv/bin/activate
pip install -r requirements.txt
python manage.py makemigrations accounts projects
python manage.py migrate
python manage.py runserver
```

Open http://127.0.0.1:8000/. **SQLite is for development only.** The final
submission must use PostgreSQL / Supabase: set `USE_SQLITE=False` in `.env`,
fill in the `DB_*` values, and run `python manage.py migrate` again.

## Setup (PostgreSQL / Supabase)

1. Create and activate a virtual environment, then install the packages:

   ```bash
   python -m venv venv
   venv\Scripts\activate          # Windows
   source venv/bin/activate       # macOS / Linux
   pip install -r requirements.txt
   ```

2. Copy `.env.example` to `.env` and fill in your secret key and database
   credentials (local PostgreSQL, or the connection details from your Supabase
   project; use `DB_SSLMODE=require` for Supabase). **Never commit `.env`.**

3. Create the database tables and run the server:

   ```bash
   python manage.py makemigrations accounts projects
   python manage.py migrate
   python manage.py runserver
   ```

4. Open http://127.0.0.1:8000/ and register a Homeowner and a Contractor account.
   (Optional) create an admin for `/admin/` with `python manage.py createsuperuser`.

## Run the tests

The test runner creates a temporary test database, so your PostgreSQL user needs
permission to create databases.

```bash
python manage.py test accounts
```

## Pages

| URL | Who | What |
| --- | --- | --- |
| `/register/` | Anyone | Create an account (choose Homeowner or Contractor) |
| `/login/` | Anyone | Log in |
| `/logout/` | Logged in (POST) | End the session |
| `/dashboard/` | Logged in | Redirects to the dashboard for your role |
| `/dashboard/homeowner/` | Homeowners only | Homeowner dashboard |
| `/dashboard/contractor/` | Contractors only | Contractor dashboard |
| `/profile/` | Logged in | View your own profile |
| `/profile/edit/` | Logged in | Edit your own profile (name, email, contact number, photo) |
| `/projects/` | Logged in | Homeowners: own projects. Contractors: assigned projects (read-only) |
| `/projects/new/` | Homeowners only | Create a renovation project |
| `/projects/<id>/` | Owner or assigned contractor | Project details |
| `/projects/<id>/edit/` | Owner only | Update a project |
| `/projects/<id>/delete/` | Owner only | Delete a project (confirmation page) |
| `/projects/budget/` | Owner or assigned contractor | View total budgets and recorded expenses |
| `/projects/<id>/budget/` | Owner or assigned contractor | Record and delete project expenses |
