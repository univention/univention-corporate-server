from collections import Counter


def analyze_ldif_file(path):
    type_counter = Counter()
    with open(path, encoding='utf-8') as file:
        object_classes = []
        for line in file:
            line = line.strip()
            if not line:
                for obj_class in object_classes:
                    type_counter[obj_class.lower()] += 1
                object_classes = []
            elif line.lower().startswith('objectclass:'):
                obj_class = line.split(':', 1)[1].strip()
                object_classes.append(obj_class)
        # Don't forget the last entry if file doesn't end with a blank line
        for obj_class in object_classes:
            type_counter[obj_class.lower()] += 1
    return type_counter


# Main program
if __name__ == "__main__":
    file_path = "zitsh-ldap.ldif"
    results = analyze_ldif_file(file_path)
    for obj_type, count in results.items():
        print(f"{obj_type}: {count}")
