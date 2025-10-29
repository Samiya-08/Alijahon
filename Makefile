mig:
	python3 manage.py makemigrations
	python3 manage.py migrate
admin:
	./manage.py createsuperuser
pip:
	pip freeze > requirements.txt
app:
	./manage.py startapp apps

makemessages:
	python3 manage.py makemessages -l en
	python3 manage.py makemessages -l uz

compile:
	python3 manage.py compilemessages