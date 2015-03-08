#!/usr/bin/make -f

.PHONY: run start stop help load
.SILENT: help

help:
	echo "Available targets:"
	echo "  start"
	echo "  stop"
	echo "  load DUMP=file.ldif"

run start:
	/usr/sbin/slapd -f slapd.conf -h ldap://127.0.0.1:1389/

stop:
	-kill `cat run/slapd.pid`

load:

load:
	/usr/sbin/slapadd -f slapd.conf -l  $(if $(DUMP),$(DUMP),$(error no DUMP=... provided))

# vim:ft=make
