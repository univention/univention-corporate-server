import base64
import csv


def decode_ldif_value(value):
    value = value.strip()
    if value.startswith("::"):
        try:
            return base64.b64decode(value[2:].strip()).decode('utf-8', errors='replace')
        except Exception:
            return f"[base64 error]: {value}"
    elif value.startswith(":"):
        try:
            return base64.b64decode(value[1:].strip()).decode('utf-8', errors='replace')
        except Exception:
            return f"[base64 error]: {value}"
    return value


def parse_ldif_file(path):
    entries = []
    current_entry = {}
    current_dn = ""
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.rstrip()
            if not line:
                if current_dn:
                    entries.append((current_dn, current_entry))
                    current_dn, current_entry = "", {}
                continue
            if line.startswith(" "):
                last_attr = list(current_entry)[-1]
                current_entry[last_attr][-1] += line[1:]
                continue
            if line.lower().startswith("dn:"):
                current_dn = decode_ldif_value(line.split(":", 1)[1])
            elif ":" in line:
                key, raw_value = line.split(":", 1)
                val = decode_ldif_value(raw_value)
                current_entry.setdefault(key.strip(), []).append(val)
        if current_dn:
            entries.append((current_dn, current_entry))
    return entries


def filter_by_objectclasses(entries, valid_classes):
    filtered = []
    for dn, entry in entries:
        classes = [v.lower() for v in entry.get("objectClass", [])]
        if any(cls in valid_classes for cls in classes):
            filtered.append((dn, entry))
    return filtered


def export_to_csv(entries, csv_path):
    with open(csv_path, "w", newline='', encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["DN", "Attribute", "Value"])
        for dn, entry in entries:
            for attr, values in entry.items():
                for v in values:
                    writer.writerow([dn, attr, v])
    print(f"✅ Exported {len(entries)} entries to {csv_path}")


#  Customize here
if __name__ == "__main__":
    ldif_file = "zitsh-ldap.ldif"
    output_csv = "filtered_ldif.csv"
    match_classes = {"organizationalunit", "groupofnames", "person"}
    print(f"🔎 Parsing {ldif_file}...")
    all_entries = parse_ldif_file(ldif_file)
    matched = filter_by_objectclasses(all_entries, match_classes)
    export_to_csv(matched, output_csv)
