DJANGO_APPS=api djcelery

export DJANGO_SETTINGS_MODULE:=plate_server.settings
export PYTHONPATH:=$(PWD):$(PYTHONPATH)

.PHONY: dbinit
dbinit:
	./bin/django-db-create
	./manage.py syncdb --noinput
	for i in $(DJANGO_APPS); do \
		./manage.py migrate $$i; \
	done
	#./manage.py loaddata plate-test.json
	./manage.py loaddata plate-auth.json
	./manage.py loaddata plate-api.json

.PHONY: pull
pull:
	git pull
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
	./manage.py dumpdata --natural --indent=3 > plate-test.json

.PHONY: dump
dump:
	./manage.py dumpdata --natural --indent=3 > plate-test.json

.PHONY: dbdestroy
dbdestroy:
	./bin/django-db-destroy

.PHONY: shell
shell:
	bash

.PHONY: deps-install deps-install-system
# install dependencies only for the current user
deps-install:
	pip install --user -r pip-requirements.txt

# install dependencies into system directories for all users
deps-install-system:
	pip install -r pip-requirements.txt
