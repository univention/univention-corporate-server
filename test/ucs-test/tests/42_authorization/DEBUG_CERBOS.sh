mkdir -p /etc/systemd/system/univention-guardian-server.service.d/

cat > /etc/systemd/system/univention-guardian-server.service.d/no-color.conf <<'EOF'
[Service]
ExecStart=
ExecStart=/usr/bin/docker-compose -f /usr/share/univention-guardian-server/docker-compose.yaml -p univention-guardian-server up --no-build --no-color
EOF

mkdir -p /etc/systemd/journald.conf.d

cat > /etc/systemd/journald.conf.d/cerbos.conf <<'EOF'
[Journal]
LineMax=4M
EOF

systemctl daemon-reload
systemctl restart systemd-journald univention-guardian-server.service

# now you can use:
#
# journalctl -u univention-guardian-server.service -f -n 0 -o json --all --output-fields=MESSAGE | jq --unbuffered '.MESSAGE | strings | split(" | ")[1:] | join(" | ") | fromjson?'
