# #!/usr/bin/env bash
# # Exit on error
# set -o errexit

# # Modify this line as needed for your package manager (pip, poetry, etc.)
# pip install -r requirements.txt

# # Convert static asset files
# python manage.py collectstatic --no-input

# # Creating Supper user on Render
# if [[ $CREATE_SUPERUSER ]];
# then
#   python manage.py createsuperuser --no-input
# fi

# # Apply any outstanding database migrations
# python manage.py migrate


#!/usr/bin/env bash
# Exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Apply database migrations
python manage.py migrate

# Collect static files (only need to do this once)
python manage.py collectstatic --no-input

# Create superuser if CREATE_SUPERUSER is set
if [[ $CREATE_SUPERUSER ]]; then
  # Use Django shell to create superuser only if it doesn't exist
  python manage.py shell -c "
from django.contrib.auth import get_user_model;
User = get_user_model();
if not User.objects.filter(username='${DJANGO_SUPERUSER_USERNAME}').exists():
    User.objects.create_superuser(
        '${DJANGO_SUPERUSER_USERNAME}',
        '${DJANGO_SUPERUSER_EMAIL}',
        '${DJANGO_SUPERUSER_PASSWORD}'
    );
    print('Superuser created successfully.');
else:
    print('Superuser already exists. Skipping creation.');
"
fi