
# Helm charts for the Univention Portal


## Usage

Copy the `*.example` files and adjust them for the current environment.

Install the charts with
`helm install <parameters> (notifications-api|portal-frontend|portal-server) ./(notifications-api|portal-frontend|portal-server)`

Add custom values with the
`--values values-(frontend|notifications-api|server).yaml`
parameter.
See
`values-(frontend|notifications-api|server).yaml.example`
files for important values.
Other changeable parameters can be found in the `values.yaml`
files of the respective project-directories.

Add a namespace-parameter to install avoid using the `default`-namespace.
I.e. `--namespace poco`


## General helm hints

See the templated output with `helm template ./portal-server/`

Remove the server-chart with `helm --namespace poco uninstall portal-server`


## General kubectl hints

Show status of the replica-set with `kubectl --namespace poco describe ReplicaSet`

Show installed Services with `kubectl --namespace poco get service`

Show running pods with `kubectl --namespace poco get pods`

Show endpoints with `kubectl --namespace poco get endpoints`

Show deployments with `kubectl --namespace poco get deployments`


## Documenting the Helm charts


The documentation of the helm charts is generated mainly out of two places:

- `values.yaml` contains the documentation of the supported configuration
  options.

- `README.md.gotmpl` is the template to generate the `README.md` file, it does
  contain additional prose documentation.

As a generator the tool `helm-docs` is in use. We support two main local usage scenarios:

- `helm-docs` runs it locally. Needs a local installation first.

- `docker compose run helm-docs` allows to use a pre-defined docker container in
  which `helm-docs` is available. Can be used in the folder `/docker` in this
  repository.
