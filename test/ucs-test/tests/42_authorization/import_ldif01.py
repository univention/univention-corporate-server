import base64
import csv
from collections import defaultdict

import chardet


def detect_encoding(file_path):
    with open(file_path, 'rb') as f:
        raw_data = f.read()
        result = chardet.detect(raw_data)
        return result['encoding'] or 'utf-8'  # fallback to utf-8


def decode_ldif_value(raw_value):
    raw_value = raw_value.strip()
    if raw_value.startswith('::'):
        return base64.b64decode(raw_value[2:].strip()).decode('utf-8', errors='replace')
    elif raw_value.startswith(':'):
        return base64.b64decode(raw_value[1:].strip()).decode('utf-8', errors='replace')
    return raw_value


def parse_ldif_file(path):
    encoding = detect_encoding(path)
    print(f"Detected encoding: {encoding}")
    entries = []
    current_entry = {}
    with open(path, encoding=encoding, errors='replace') as file:
        for line in file:
            line = line.rstrip()
            if not line:
                if current_entry:
                    entries.append(current_entry)
                    current_entry = {}
                continue
            if ':' in line:
                key, raw_value = line.split(':', 1)
                value = decode_ldif_value(raw_value)
                current_entry.setdefault(key.strip(), []).append(value)
        if current_entry:
            entries.append(current_entry)
    return entries


def extract_dn_groups(entries):
    groups = defaultdict(list)
    for entry in entries:
        dn = entry.get('dn', [''])[0]
        group_key = None
        for segment in dn.split(','):
            if segment.strip().lower().startswith('ou='):
                group_key = segment.strip()
                break
            elif segment.strip().lower().startswith('dc=') and not group_key:
                group_key = segment.strip()
        if not group_key:
            group_key = 'UNGROUPED'
        groups[group_key].append(dn)
    return groups


def export_to_csv(groups, filename='dn_groups.csv'):
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Group', 'Distinguished Name'])
        for group, dns in groups.items():
            for dn in dns:
                writer.writerow([group, dn])


# 🏁 Run the parser
if __name__ == "__main__":
    file_path = 'zitsh-ldap.ldif'
    entries = parse_ldif_file(file_path)
    grouped_dns = extract_dn_groups(entries)
    export_to_csv(grouped_dns)
    print("✅ Done: Exported grouped DNs to dn_groups.csv using detected encoding.")
