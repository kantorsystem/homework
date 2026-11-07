# Code Review

Hi! Good start, the structure is there (app folder, Helm chart, Terraform, CI), so most of the work
is wiring things together. Below are the 5 things I would fix first, in this order. With 1 and 2
fixed you can already deploy and iterate, 3 to 5 make it stable and maintainable.

## 1. The Helm resources don't connect to each other, so the app is not reachable at all

Even if the pod starts, no request can reach it, because the references between the files are broken:

- `templates/service.yaml`: the selector is `app: myapps`, but the pod label in
  `templates/deployment.yaml` is `app: myapp`. The Service finds no pods, so it has no endpoints.
- `templates/ingress.yaml`: the backend points to a service called `homeworks`, which does not exist.
  The Service is called `myapp`.
- `templates/deployment.yaml`: `containerPort` is `5000`, but the Service `targetPort` and the app use `8080`.

**How to fix:** put the files next to each other (VS Code split view helps) and follow one request
through them: Ingress → Service name and port → Service selector → pod labels → container port.
Every arrow has to match. Once you see the chain, the fixes are one line each.

**Tip:** `helm lint` will not catch this, the YAML itself is valid. Run `helm template` to see what is
really rendered, install it on a local cluster (kind / minikube) and check
`kubectl get endpoints myapp`. An empty list means the selector is wrong.

## 2. The Terraform code does not validate

`terraform/main.tf` cannot run in its current state:

- `value = ` for `image.tag` is empty.
- `value = prod` is not a string, Terraform reads it as a reference to something that does not exist.
- `chart = "../helm/homework"` points to a folder that does not exist, the chart is in `helm/`.

**How to fix:** use the variables you already declared (`var.image_tag`, `var.environment`) and point
the chart to `"${path.module}/../helm"`. `path.module` makes the path relative to the `.tf` file and
not to the folder you run Terraform from.

**Tip:** always run `terraform fmt` and `terraform validate` before you commit. They take a second
and show exactly this kind of error.

## 3. Nothing is pinned to a version

- `terraform/providers.tf` has no `required_providers` block, so `terraform init` always downloads the
  newest provider. The helm provider v3 changed the syntax of `set {}` and `kubernetes {}`, so this
  code already breaks today without anyone touching it.
- `helm/values.yaml` uses the `latest` image tag. You never know which version is running, you cannot
  roll back, and Kubernetes always tries to pull it (on kind this fails with `ImagePullBackOff`).

**How to fix:** add `required_providers` with `source` and a version constraint like `~> 2.17`
(allows minor updates, blocks the next major) and commit `.terraform.lock.hcl`. For images use a
real tag, for example the commit SHA from CI.

**Tip:** the rule is the same everywhere: a major update can bring syntax or parameter changes, so
upgrades should be a decision, not an accident.

## 4. Values and variables are defined but not used, everything is hardcoded

- `values.yaml` has `replicaCount` and `service.port`, but the templates use `replicas: 1` and a fixed port.
- `terraform/variables.tf` declares `namespace`, `environment` and `image_tag`, but `main.tf` uses
  none of them, and the namespace is hardcoded to `production`.

This is misleading: it looks configurable, but changing a value does nothing. You cannot scale the
app or deploy it to another environment without editing templates.

**How to fix:** every value in `values.yaml` should be used in a template (`{{ .Values.replicaCount }}`),
and every Terraform variable should be referenced (`var.namespace`). Add a `description` to each
variable so others know what it is for.

**Tip:** `tflint` warns about unused variables.

## 5. The CI pipeline only has two `echo` steps

`.gitlab-ci.yml` has a `build` and a `deploy` job, but they don't build or deploy anything, and there
is no place where the code is checked.

**How to fix:** split the pipeline into stages and small jobs, so when something fails you see
immediately where:

- `lint`: separate jobs for hadolint, `helm lint` / `helm template`, `terraform fmt -check` / `validate`
- `test`: unit tests of the app
- `build`: build the image and push it with the commit SHA as tag
- `deploy`: `helm upgrade --install --wait` with that tag, only from the main branch

Use a pinned image for each job. A lint stage like this would have caught points 1–4 on the first push.

---

Fix 1 and 2 first and get it running on a local cluster, then 3 and 4, and finally the pipeline.
Happy to pair on any of these if you get stuck!
