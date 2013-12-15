DJANGO_APPS=api

.PHONY: dbinit
dbinit:
	./manage.py syncdb --noinput
	./manage.py migrate $(DJANGO_APPS)
	./manage.py loaddata plate-test.json

.PHONY: pull
pull:
	git pull
	./manage.py migrate --merge $(DJANGO_APPS)

# dbdump: run after DB schema changes
.PHONY: dbschemachange
dbschemachange:
	./manage.py schemamigration --auto $(DJANGO_APPS)
	./manage.py migrate --db-dry-run $(DJANGO_APPS)
	./manage.py migrate $(DJANGO_APPS)
	./manage.py dumpdata --indent=3 api > plate-test.json
