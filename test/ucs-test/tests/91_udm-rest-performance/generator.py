# read the openapi.json file and generate locustfiles
import argparse
import json
import os

import requests


def read_json(path):
    with open(path) as f:
        return json.load(f)


def replace_refs(value, original_json):
    # find all dictionaries with a $refs key
    if isinstance(value, dict):
        if "$ref" in value:
            new_value = original_json
            for x in value["$ref"].split("/")[1:]:
                new_value = new_value[x]
            return replace_refs(new_value, original_json)
        else:
            return {k: replace_refs(v, original_json) for k, v in value.items()}
    elif isinstance(value, list):
        return [replace_refs(val, original_json) for val in value]
    return value


def generate_body(body_schema):
    if body_schema is None:
        return None
    body = {}
    if "properties" not in body_schema:
        return body
    for key, value in body_schema["properties"].items():
        if "type" not in value:
            continue
        if value["type"] == "string":
            body[key] = value.get("example", "string")
        elif value["type"] == "integer":
            body[key] = value.get("example", 1)
        elif value["type"] == "array":
            items = value.get("items", {})
            body[key] = [items.get("example", items.get("type", "string"))]
        elif value["type"] == "object":
            body[key] = generate_body(value)
    return body


def main():
    # this script can receive 2 arguments:
    # 1. username
    # 2. password
    # 3. host
    parser = argparse.ArgumentParser(
        description="Generate locustfiles from the openapi.json file."
    )
    parser.add_argument(
        "--username",
        help="The username to use for the locustfiles.",
        default="Administrator",
    )
    parser.add_argument(
        "--password",
        help="The password to use for the locustfiles.",
        default="univention",
    )
    parser.add_argument(
        "--host",
        help="The host to use for the locustfiles.",
        default="localhost",
    )
    args = parser.parse_args()
    username = args.username
    password = args.password
    host = args.host

    openapi = requests.get(f"http://{username}:{password}@{host}/univention/udm/openapi.json", headers={"Accept": "application/json"}).json()
    # generate a folder for each tag
    openapi = replace_refs(openapi, openapi)
    print("$ref" in str(openapi))
    tasks = {}

    for path, path_data in openapi["paths"].items():
        url = path
        if "{" in url:
            url = f"f'/univention/udm{url}'"
        else:
            url = f"'/univention/udm{url}'"
        path_params = []
        for param in path_data.get("parameters", []):
            if param["in"] == "path":
                path_params.append(f"{param['name']} = {param.get('example', 'string')!r}  # {param['description']}")
        for method, method_data in path_data.items():
            # print("=====================================")
            # print(method, method_data)
            # print("=====================================")
            if method not in ["get", "post", "put", "patch", "delete"]:
                continue

            # generate a folder for each tag inside of tasks
            if method_data["tags"][0] not in ["users/user", "container/ou", "groups/group", "computers/domaincontroller_slave"]:
                continue
            tag = method_data["tags"][0].replace("/", "_")
            tag_path = os.path.join("locustfiles/tasks", tag)
            if not os.path.exists(tag_path):
                os.makedirs(tag_path)

            # generate a file for each endpoint inside of the tag folder
            filename = path.replace("/", "_").replace("{", "").replace("}", "") + f"_{method}.py"
            filename = filename.replace("__", "_")
            if filename.startswith("_"):
                filename = filename[1:]
            filename_path = os.path.join(tag_path, filename)
            tasks.setdefault(tag, []).append(filename.replace(".py", ""))

            with open(filename_path, "w") as f:
                f.write(f"# {method_data['summary']}" + "\n")
                f.write(f"# {method_data.get('description', 'Empty description')}" + "\n")
                f.write("# # this file implements the Locust task for the following endpoints:\n")
                f.write(f"# # - {method.upper()} {path}" + "\n")
                f.write("#\n\n\n")
                f.write(f"def {filename.replace('.py', '')}(self):" + "\n")
                f.write(f'    \"\"\"{method.upper()} {path}\"\"\"' + "\n")
                params = {}
                if url.startswith("f'"):
                    for param in path_params:
                        f.write(f"    {param}" + "\n")
                for param in method_data.get("parameters", []):
                    params.setdefault(param["in"], []).append(param)
                for param_type, param_list in params.items():
                    f.write(f"    # {param_type} parameters for this endpoint" + "\n")
                    f.write(f"    {param_type} = {{" + "\n")
                    for param in param_list:
                        f.write(f"        {param['name']!r}: {param.get('example', '')!r},  #{' ' + param['description'] if param['description'] else ''} ({param['schema']['type']})" + "\n")
                    f.write("    }" + "\n")

                body = None
                if "requestBody" in method_data:
                    body = method_data["requestBody"]
                    if "content" in body:
                        body = body["content"]["application/json"]["schema"]

                    f.write("    # body for this endpoint" + "\n")
                    body = json.dumps(generate_body(body), indent=4)
                    body_lines = body.splitlines()
                    f.write("    data = {\n")

                    for line in body_lines[1:-1]:
                        f.write(f"    {line}" + "\n")
                    f.write("    }\n")
                response_codes = method_data["responses"].keys()
                response_codes = [int(code) for code in response_codes if code.startswith("2")]
                f.write(
                    f"    self.request({method!r}, {url}, name={path!r}"
                    f"{', headers=header' if 'header' in params else ''}"
                    f"{', params=query' if 'query' in params else ''}"
                    f"{', json=data' if body else ''}"
                    f", verify=False, response_codes={response_codes!r})"
                    "\n"
                )
    # create locustfile.py
    for tag, task_list in tasks.items():
        with open(f"locustfiles/udm_{tag}_locust_user.py", "w") as f:
            f.write("from generic_user import GenericUser\n")
            for task in task_list:
                f.write(f"from tasks.{tag}.{task} import {task}" + "\n")
            f.write("\n")
            f.write(f"tag = {tag.replace('_','/')!r}" + "\n")
            f.write("\n\n")
            for task in task_list:
                # generate class name in CamelCase
                classname = "".join([x.capitalize() for x in task.split("_")])
                f.write(f"class {classname}(GenericUser):\n")
                f.write(f"    tasks = [{task}]\n")
                f.write("    tag = tag\n")
                if task != task_list[-1]:
                    f.write("\n\n")

    with open("template.txt") as f:
        contents = f.read()

    # locust_file, locust_user_class, locust_run_time, url_name, rps, time_95_percentile
    pytest_params = []
    for tag, task_list in tasks.items():
        for task in task_list:
            # generate class name in CamelCase
            classname = "".join([x.capitalize() for x in task.split("_")])
            locust_file = f"udm_{tag}_locust_user.py"
            url_name = f"/univention/udm/{'/'.join(task.split('_')[:-1])}"
            pytest_params.append((locust_file, classname, url_name, "1m", 0.5, 2000))
    with open("01_udm_performance_test.py", "w") as f:
        str_pytest_params = ",\n".join([f"    {x!r}" for x in pytest_params])
        print(str_pytest_params)
        f.write(contents.format(params=str_pytest_params))


if __name__ == "__main__":
    main()
