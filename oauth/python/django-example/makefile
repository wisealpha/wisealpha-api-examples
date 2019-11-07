default: run

createsuperuser:
	cd examplesite && python manage.py createsuperuser --settings=examplesite.settings

syncdb:
	cd examplesite && python manage.py syncdb --settings=examplesite.settings

makemigrations:
	cd examplesite && python manage.py makemigrations $(app) --settings=examplesite.settings

migrate:
	cd examplesite && python manage.py migrate --settings=examplesite.settings

run:
	cd examplesite && python manage.py runserver 0.0.0.0:9090 --settings=examplesite.settings

shell:
	cd examplesite && python manage.py shell --settings=examplesite.settings