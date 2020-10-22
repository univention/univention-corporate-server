#!/bin/bash

umc_parallel=$1

a2enmod proxy_balancer
a2enmod lbmethod_bybusyness

trap "kill 0; ucr unset umc/parallel; ucr commit /etc/apache2/sites-available/univention.conf; systemctl restart apache2" EXIT

for ((i=0; i<umc_parallel; i++)); do
	univention-management-console-server -n -p "$((6681 + i))" &
	univention-management-console-web-server -n -p "$((8101 + i))" &
done
ucr set umc/parallel="$umc_parallel"
ucr commit /etc/apache2/sites-available/univention.conf
systemctl restart apache2
echo "ready to go"
wait
