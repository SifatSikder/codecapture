# codecapture

python3.13 -m django startproject codecapture_backend
cd codecapture_backend
python3.13 manage.py startapp api
python3.13 manage.py runserver
python3.13 manage.py migrate

pip install django-cors-headers
