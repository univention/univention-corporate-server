# -*- mode: Python -*-

config.define_string(
    "univention-project-username",
    args=False,
    usage="Username for Univention project at gitlab.souvap-univention.de"
)
config.define_string(
    "gitlab-access-token",
    args=False,
    usage="Access token from gitlab.souvap-univention.de with read_registry and write_registry scope"
)
cfg = config.parse()

univention_project_username = cfg.get("univention-project-username")
if not univention_project_username:
    print("Please specify a username for the Univention project at gitlab.souvap-univention.de")
    exit("No username specified")

gitlab_access_token = cfg.get("gitlab-access-token")
if not gitlab_access_token:
    print("Please specify an access token from gitlab.souvap-univention.de with read_registry scope")
    exit("No access token specified")

# Defaults to `gaia` cluster
# TODO: make this configurable
allow_k8s_contexts('kubernetes-admin@cluster.local')

namespace = k8s_namespace()
if namespace == 'default':
    print("Please specify a namespace in the Kubeconfig")
    exit("No namespace specified")

docker_build(
    'registry.souvap-univention.de/souvap/tooling/images/univention-portal/portal-server:development',
    './',
    dockerfile='docker/portal-server/Dockerfile',
)

docker_build(
    'registry.souvap-univention.de/souvap/tooling/images/univention-portal/portal-consumer:development',
    './',
    build_args={
        'PORTAL_BASE_IMAGE': 'registry.souvap-univention.de/souvap/tooling/images/univention-portal/portal-server:development',
    },
    dockerfile='docker/portal-consumer/Dockerfile',
)

docker_build(
    'registry.souvap-univention.de/souvap/tooling/images/univention-portal/portal-frontend:development',
    './frontend',
    dockerfile='frontend/Dockerfile',
)

local("""
    kubectl get secret --namespace {namespace} | grep souvap-gitlab || \
    kubectl create secret docker-registry souvap-gitlab --docker-server=registry.souvap-univention.de --docker-username={univention_project_username} --docker-password={gitlab_access_token} -n {namespace}
    """.format(
    univention_project_username=univention_project_username,
    gitlab_access_token=gitlab_access_token,
    namespace=namespace
))

local("helm get values ums-portal-frontend --namespace {namespace} > portal-frontend-values.yaml".format(namespace=namespace))
local("helm get values ums-portal-server --namespace {namespace} > portal-server-values.yaml".format(namespace=namespace))
local("helm get values ums-portal-consumer --namespace {namespace} > portal-consumer-values.yaml".format(namespace=namespace))

k8s_yaml(
    helm(
        "helm/portal-frontend",
        name='ums-portal-frontend',
        namespace=namespace,
        values='portal-frontend-values.yaml',
        set=[
            'global.imagePullSecrets[0]=souvap-gitlab',
            'image.imagePullPolicy=Always',
            'image.registry=registry.souvap-univention.de',
            'image.repository=souvap/tooling/images/univention-portal/portal-frontend',
            'image.tag=development',
        ]
    )
)
k8s_yaml(
    helm(
        "helm/portal-server",
        name='ums-portal-server',
        namespace=namespace,
        values='portal-server-values.yaml',
        set=[
            'global.imagePullSecrets[0]=souvap-gitlab',
            'image.imagePullPolicy=Always',
            'image.registry=registry.souvap-univention.de',
            'image.repository=souvap/tooling/images/univention-portal/portal-server',
            'image.tag=development',
        ]
    )
)
k8s_yaml(
    helm(
        "helm/portal-consumer",
        name='ums-portal-consumer',
        namespace=namespace,
        values='portal-consumer-values.yaml',
        set=[
            'global.imagePullSecrets[0]=souvap-gitlab',
            'image.imagePullPolicy=Always',
            'image.registry=registry.souvap-univention.de',
            'image.repository=souvap/tooling/images/univention-portal/portal-consumer',
            'image.tag=development',
        ]
    )
)
