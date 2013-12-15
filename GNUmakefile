DJANGO_APPS=api djcelery

.PHONY: dbinit
dbinit:
	./manage.py syncdb --noinput
	for i in $(DJANGO_APPS); do \
		./manage.py migrate $$i; \
	done
	./manage.py loaddata plate-test.json

.PHONY: pull
pull:
	git pull
	./manage.py migrate --merge $(DJANGO_APPS)
	for i in $(DJANGO_APPS); do \
		./manage.py migrate --merge $$i; \
	done

# dbdump: run after DB schema changes
.PHONY: dbschemachange
dbschemachange:
	for i in $(DJANGO_APPS); do \
		./manage.py schemamigration --auto $$i; \
	done
	for i in $(DJANGO_APPS); do \
		./manage.py migrate --db-dry-run $$i; \
	done
	for i in $(DJANGO_APPS); do \
		./manage.py migrate $$i; \
	done
	./manage.py dumpdata --indent=3 api > plate-test.json
