#!/bin/sh

if [ -f /etc/crontab ]; then
	touch /etc/crontab
fi

if [ -d /etc/cron.d ]; then
	touch /etc/cron.d/*
fi
