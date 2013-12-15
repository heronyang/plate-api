.PHONY: dbinit
dbinit:
	./manage.py syncdb --noinput
	./manage.py migrate

.PHONY: pull
pull:
	git pull
	./manage.py migrate --merge
