#!/usr/bin/env bash
# Exit on error
set -o errexit

# Modify this line as needed for your package manager (pip, poetry, etc.)
pip install -r requirements.txt

# Convert static asset files
python manage.py collectstatic --no-input

# Creating Supper user on Render
if [[ $CREATE_SUPERUSER ]];
then
  python manage.py createsuperuser --no-input
fi

# Apply any outstanding database migrations
python manage.py migrate

# Collect static files