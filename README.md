# DevOps Engineer Homework

## Goals

## Goal 1

Complete and improve the provided project.

The repository contains the following files:

- Incomplete application code
- Broken/incomplete terraform configuration
- Incomplete Helm Chart
- Incomplete Gitlab CI pipeline

### Requirements

#### Application

Implement a simple application in either:

- Go
- Python

The application must expose the following endpoints:

##### `GET /health`

**Response:**

```json
{
    "status": "ok"
}
```

##### `GET /version`

**Response:**

```json
{
    "version": "1.0.0"
}
```

##### `GET /env`

**Response:**

```json
{
    "environment": "<value from ENVIRONMENT variable>"
}
```

##### `POST /config`

**Request:**

```json
{
    "name": "database_url",
    "value": "postgres://example"
}
```

**Response:**

```json
{
    "name": "database_url",
    "value": "postgres://example"
}
```

##### `GET /config/{name}`

**Example:**

```bash
GET /config/database_url
```

**Response:**

```json
{
    "name": "database_url",
    "value": "postgres://example"
}
```

##### `DELETE /config/{name}`

**Response:**

```json
{
    "deleted": true
}
```

#### Containerization

- Create the necessary Dockerfile with minimal setup

#### Terraform

- Review and fix/complete the Terraform code

#### Helm

- Review and fix/complete the Helm Chart

#### Gitlab CI

- Complete the pipeline so it becomes capable of building and deploying the application

### Deliverables

- Source Code of the Go/Python application
- Dockerfile
- Terraform changes
- Helm changes
- CI pipeline changes
- README describing decisions, assumptions and user guide for the project.

### Notes

You are not expected to deploy to a cloud provider.
The solution should work with a local Kubernetes cluster such as:

- Kind
- Minikube
- K3d

### Timing

Timebox yourself to approximately **3 hours**. If you can't finish the work within the timebox, describe in the README.md what is left and how you would approach it.

## Goal 2

You get this half-baked project from one of your colleagues who is a Junior and asking for your guidance.

Provide a short code review in `REVIEW.md` where you address the **top 5 most important things** to fix so the colleague can move forward.

### Review Timing

Spend no more than **30 minutes** on review and feedback.
