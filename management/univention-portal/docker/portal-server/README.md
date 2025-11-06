# Univention Portal Server Image

The `Dockerfile` in this folder does define the image for the containerized
version of the Portal Server component.


## Configuration handling

The Portal Server does expect its configuration to be inside of a JSON file
which is typically called `config.json`.

The script [`docker-entrypoint.sh`](./docker-entrypoint.sh) does contain logic
which will generate this configuration file on container start and inject values
based on environment variables. This approach shall provide a bridge into
container best practices, so that most configuration is consistently provided
based on environment variables.
