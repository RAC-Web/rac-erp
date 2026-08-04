$ErrorActionPreference = 'Stop'
python -m venv venv
.\venv\Scripts\activate
python -m pip install --upgrade pip
pip install django djangorestframework psycopg2-binary pillow django-crispy-forms crispy-bootstrap5 django-htmx reportlab openpyxl gunicorn python-dotenv

# Start project named config
python -m django startproject config .

mkdir apps
cd apps
python -m django startapp accounts
python -m django startapp students
cd ..

Write-Output "Setup Complete!"
