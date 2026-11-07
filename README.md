# DevOps Homework – Solution

This repo contains a small Flask config service with a Dockerfile, Helm chart, Terraform code and a
GitLab CI pipeline. The original task description is in [TASK.md](TASK.md).

I started with the application, then went through the Dockerfile, Helm chart, Terraform and CI one
by one, and tested each part locally on a kind cluster before moving on to the next one.

## User Guide

### Prerequisites
Python 3.13, Docker, kind, kubectl, Helm, Terraform (optional: hadolint, tflint).

### Run locally
```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .\.venv\Scripts\Activate.ps1
pip install -r app/requirements.txt pytest
python app/app.py                # http://localhost:8080
pytest app/ -v                   # unit tests
```

### Run with Docker
```bash
docker build -t myapp:dev app/
docker run --rm -p 8080:8080 -e ENVIRONMENT=docker myapp:dev
curl localhost:8080/health
```

### Deploy to kind with Helm
```bash
kind create cluster --name homework
kind load docker-image myapp:dev --name homework
helm upgrade --install myapp helm/ --namespace dev --create-namespace --wait
kubectl port-forward -n dev svc/myapp 8080:80   # kind has no Ingress controller
```

### Deploy to kind with Terraform
```bash
terraform -chdir=terraform init
terraform -chdir=terraform apply \
  -var="image_tag=dev" -var="environment=dev" -var="namespace=homework-dev"
```

### CI/CD
The pipeline runs `lint`, `test`, `build` and `deploy`. To deploy, GitLab needs a CI/CD variable
called `KUBECONFIG` (type File) with access to the cluster. Registry credentials come from GitLab.

### API
| Method | Path | Response |
|---|---|---|
| GET | `/health` | `{"status": "ok"}` |
| GET | `/version` | `{"version": "1.0.0"}` |
| GET | `/env` | `{"environment": "<ENVIRONMENT>"}` |
| POST | `/config` | `{"name": ..., "value": ...}`, 400 if a field is missing |
| GET | `/config/{name}` | `{"name": ..., "value": ...}`, 404 if not found |
| DELETE | `/config/{name}` | `{"deleted": true}`, or 404 with `{"deleted": false}` |

---

## What You Changed

### Application
- I wrote the service in Python with Flask. It is lightweight and easy to read, which is enough for
  a service this small.
- Config values are kept in an in-memory dict, separate from the app's own settings.
- Basic error handling: a missing field in `POST /config` returns 400, an unknown key on GET or
  DELETE returns 404.
- `APP_VERSION` and `ENVIRONMENT` are read from environment variables, so Helm can set them
  without code changes.
- Dependency versions are pinned in `requirements.txt` so builds are reproducible.
- Added 5 pytest tests in `app/test_app.py` using Flask's test client.

### Docker
- Base image is `python:3.13-slim`, the same Python version I used locally.
- `requirements.txt` is copied and installed before the code, so the dependency layer stays cached
  when only the code changes. `--no-cache-dir` keeps the image smaller.
- The app runs as a non-root user with a fixed UID (10001). Kubernetes can only check
  `runAsNonRoot` with a numeric UID.
- gunicorn serves the app on port 8080 instead of the Flask dev server. The `CMD` is in exec form, so
  gunicorn gets `SIGTERM` and shuts down cleanly. It runs with one worker, because every worker would
  have its own in-memory store.

### Helm
Bugs I fixed:
- The Service selector was `app: myapps`, but the pod label is `app: myapp`. Because of this the
  Service had no endpoints, even though the pod was running.
- The Ingress pointed to a service called `homeworks`, which does not exist. Changed it to `myapp`.
- `containerPort` was 5000, but the app listens on 8080.
- The image tag was `latest`, I changed it to `dev`. With `latest` Kubernetes uses
  `imagePullPolicy: Always`, which fails on kind because there is no registry (`ImagePullBackOff`).

Things I added:
- `replicas` now comes from `replicaCount` in `values.yaml`, before it was hardcoded.
- Readiness and liveness probes on `/health`. Readiness takes the pod out of traffic, liveness
  restarts it. Liveness starts a bit later so a slow startup does not cause a restart loop.

### Terraform
- The chart path `../helm/homework` did not exist, I changed it to `${path.module}/../helm`.
  `path.module` is relative to the `.tf` files and not to the current directory, so it also works
  with `-chdir` and in CI.
- `image.tag` had an empty value and `environment` used `prod` without quotes, which is an invalid
  reference. Both now use the variables (`var.image_tag`, `var.environment`).
- The namespace was hardcoded to `production`, now it uses `var.namespace`. All variables are used now.
- The most important fix: there was no `required_providers` block, so `terraform init` downloaded
  helm provider v3. Version 3 changed the `set {}` and `kubernetes {}` syntax, so the existing code
  broke. I pinned both providers to `~> 2.17` (2.x updates are allowed, 3.0 is not) and committed
  `.terraform.lock.hcl`.
- Added descriptions to the variables, an `outputs.tf` (namespace, release name, image tag) and ran
  `terraform fmt`.
- Added `.terraform/` and `*.tfstate` to `.gitignore`. The state can contain secrets and should not
  be in git.

### GitLab CI
- lint: three jobs that run in parallel (hadolint, `helm lint` and `helm template`,
  `terraform fmt`, `init` and `validate`).
- test: runs the pytest tests.
- build: builds the image and pushes it to the GitLab registry as
  `$CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA`.
- deploy: `helm upgrade --install --namespace dev --create-namespace --wait`, only on the default
  branch, as GitLab environment `dev`.

Some decisions:
- Every image is pinned to a version, none of them use `latest`.
- The terraform and helm images need `entrypoint: [""]`. Their entrypoint is the tool itself, so
  without this the runner cannot start its shell script.
- The image tag is the commit SHA and not the branch name. This way every image belongs to exactly
  one commit and I can roll back.
- The registry password is passed with `--password-stdin`, so it does not show up on the command line.
- I deploy with Helm and not with Terraform. Terraform in CI would need a remote state backend,
  Helm does not need state. Terraform is used for setting up the environment.
- With `--wait` the job fails if the pods don't pass the readiness probe.

### How I tested it
- App: curl against all endpoints locally, in Docker and in kind. pytest: 5 passed.
- Docker: hadolint has no findings, the container runs as `uid=10001`.
- Helm: `helm lint` and `helm template`, then installed on kind. The pod is running, the Service
  has an endpoint and both probes are active.
- Terraform: `validate`, `fmt` and `tflint` are clean. `terraform apply` on kind works and the
  `ENVIRONMENT` value reaches the pod.
- CI: I could not run it on a real GitLab runner. I checked the syntax with `gitlab-ci-local` and ran
  every job locally with the same image and script. Build and deploy were tested against kind, but
  without registry login and push.

---

## Assumptions
- A local kind cluster is enough, nothing is deployed to the cloud.
- There is no local registry, images are loaded with `kind load`. CI uses the GitLab registry.
- Config values don't need to survive a restart, the task does not ask for persistence.
- There is one environment (`dev`). The variables are ready for more.
- The GitLab runner uses the Docker executor with privileged mode for docker-in-docker.

## Known Limitations
- In-memory store: data is lost on restart and not shared between replicas or workers, so the app
  is limited to 1 replica and 1 worker.
- If the body of `POST /config` is not valid JSON, Flask returns its HTML 400 page instead of a JSON
  error. An empty string is also rejected as a value.
- Ingress: kind has no Ingress controller. The host is hardcoded, there is no `ingressClassName`
  and the Ingress cannot be disabled.
- Helm: resource names are hardcoded (`myapp`), so two releases in one namespace would collide.
  The `service.port` value is not used. No `resources`, `securityContext` or explicit
  `imagePullPolicy`.
- Terraform: local state without locking. The kubeconfig path is fixed and no context is set, so it
  deploys to whatever cluster is currently active. Providers are still on v2.
- CI: not run on real GitLab, so login, push and the branch rule are not tested. No caching and no
  prod environment.

## Production Improvements
- Storage: use a database or Redis instead of the in-memory dict. Then the app is stateless and
  can run with more replicas, HPA and a PodDisruptionBudget.
- App: JSON errors everywhere, input validation, structured logging, a metrics endpoint, and
  separate liveness and readiness endpoints once there are external dependencies.
- Docker: pin the base image by digest, scan images (e.g. Trivy), smaller multi-stage or
  distroless image.
- Helm: names based on the release name, standard `app.kubernetes.io/*` labels, `resources`,
  `securityContext`, configurable Ingress, one values file per environment, and publish the chart
  to an OCI registry.
- Terraform: remote state with locking (e.g. GitLab-managed state), separate state and tfvars per
  environment, variable validation, kube context as a variable, and move to provider v3.
- CI/CD: manual prod deploy from protected branches, Terraform plan on merge requests and apply on
  main, security scanning, `needs` and caching, Kaniko instead of privileged dind, the GitLab
  Kubernetes agent instead of a static kubeconfig, and automatic rollback with `--atomic`.
- Operations: monitoring and alerting, central logging, and secrets from a secret manager such as
  Vault or External Secrets.

---

## AI usage
I used an AI assistant as a reviewer and for explanations while working, and to translate and
structure this README from my own notes. All changes were made, tested and decided by me.
