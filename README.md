# Credit Data Generator 🏦📊

> **Synthetic credit datasets at scale, powered by a custom GAN and a cloud‑native big‑data pipeline.**

![CI](https://github.com/your‑org/credit‑data‑generator/actions/workflows/ci.yml/badge.svg)
![License](https://img.shields.io/github/license/your‑org/credit‑data‑generator)
![K8s](https://img.shields.io/badge/kubernetes‑ready-✔️‑blue)

---

## Table of Contents
1. [Overview](#overview)
2. [Key Features](#key-features)
3. [Architecture](#architecture)
4. [Quick Start](#quick-start)
5. [Deployment Guide](#deployment-guide)
6. [CI/CD Pipeline](#cicd-pipeline)
7. [Tech Stack](#tech-stack)
8. [Repository Layout](#repository-layout)
9. [Contributing](#contributing)
10. [License](#license)

---

## Overview
This project **automatically generates high‑fidelity, fully‑anonymised credit datasets** using a *Generative Adversarial Network* (GAN) trained on domain‑specific credit features. The data generation is orchestrated by a *big‑data pipeline* that scales elastically on Kubernetes and is fully reproducible via Infrastructure‑as‑Code (IaC).

> **Why?**
> - Enable data‑hungry modelling teams to experiment safely with synthetic credit data.
> - Provide an opinionated, end‑to‑end template to practise K8s, MLOps and cloud engineering.

---

## Key Features
- **Custom GAN Model** – PyTorch‑based architecture tuned for tabular credit features.
- **Scalable Data Pipeline** – Apache Spark (or Beam) jobs packaged as Docker images and run as K8s jobs.
- **End‑to‑End MLOps** – Training, validation, and inference orchestrated by Kubeflow Pipelines.
- **IaC First** – All cloud resources (VPC, K8s cluster, storage buckets) provisioned via Terraform.
- **CI/CD** – GitHub Actions deploys code, containers, and infra on every push.
- **Observability** – Prometheus + Grafana dashboards for model & pipeline metrics.
- **Security & Compliance** – Synthetic data ensures no PII leakage; secrets managed with Vault.

---

## Architecture
```
┌───────────────┐      ┌────────────────┐      ┌──────────────────┐
│  Source Data  │──▶──▶│   GAN Trainer  │──▶──▶│ Model Registry    │
└───────────────┘      └────────────────┘      └────────┬─────────┘
                           ▲                             │
                           │                             │
                           │           ┌─────────────────▼────────────────┐
                           │           │   Data Generation Spark Jobs      │
                           │           └─────────────────┬────────────────┘
                           │                             │
                           │                             ▼
                    ┌──────┴──────┐               ┌─────────────┐
                    │  Feature    │               │ Object      │
                    │  Store      │               │ Storage     │
                    └─────────────┘               └─────────────┘
```
> See `docs/architecture.png` for the full diagram.

---

## Quick Start
```bash
# 1. Clone & enter repo
$ git clone https://github.com/your‑org/credit‑data‑generator.git
$ cd credit‑data‑generator

# 2. Spin up a local K8s cluster (kind or minikube)
$ make k8s‑up

# 3. Build & load Docker images
$ make docker‑build

# 4. Run a smoke test that trains a tiny GAN and generates 1 k records
$ make quick‑start
```
The command above launches a Kubeflow pipeline that:
1. Ingests a sample CSV.
2. Trains the GAN for 2 epochs.
3. Generates 1 000 synthetic rows into `./output/synthetic.csv`.

---

## Deployment Guide
### Prerequisites
| Tool | Minimum Version | Purpose |
|------|-----------------|---------|
| Terraform | 1.7 | IaC provisioning |
| kubectl | 1.30 | K8s control |
| Helm | 3.15 | Package charts |
| Docker | 26.1 | Container runtime |
| Python | 3.11 | GAN training & CLI |

### 1️⃣ Provision Infra
```bash
# Edit variables.tf to match your cloud account
$ terraform init && terraform apply
```
### 2️⃣ Deploy Kubernetes Stack
```bash
$ helm dependency update charts/platform
$ helm install platform charts/platform -n platform --create-namespace
```
### 3️⃣ Kick off Pipeline
```bash
$ kubectl apply -f k8s/pipelines/run‑full.yaml
```
Monitor progress in *Kubeflow Central Dashboard → Runs*.

---

## CI/CD Pipeline
| Stage | Trigger | What Happens |
|-------|---------|--------------|
| **Lint & Test** | PR open/push | `pytest`, `ruff`, `yamllint` |
| **Build Images** | Merge → main | Build & push versioned Docker images │
| **Apply IaC** | Tag release | Terraform plan + apply to prod account |
| **Deploy K8s** | Tag release | Helm upgrade of live cluster |

Workflows live in `.github/workflows/` – feel free to copy or adapt.

---

## Tech Stack
- **Machine Learning**: Python 3 · PyTorch 2 · scikit‑learn · Weights & Biases
- **Data Processing**: Apache Spark 4 / Google Dataflow · Parquet
- **Orchestration**: Kubeflow Pipelines · Argo Workflows
- **Infrastructure**: Kubernetes 1.30 · Terraform v1 · Helm v3
- **CI/CD**: GitHub Actions · Docker Buildx
- **Observability**: Prometheus · Grafana · Loki · Jaeger

---

## Repository Layout
```
.
├── charts/            # Helm charts
├── data/              # Sample raw datasets (small)
├── docs/              # Diagrams & ADRs
├── kubeflow/          # Pipeline definitions
├── model/             # GAN architecture & training scripts
├── pipeline/          # Spark jobs & DAG code
├── terraform/         # IaC modules
└── .github/           # CI/CD workflows
```

---

## Contributing
1. **Fork** the repository and create your feature branch (`git checkout -b feat/amazing‑feature`).
2. Run `make pre‑commit` to ensure tests & linters pass.
3. Submit a Pull Request – describe *what* & *why* clearly.

All contributions (code, docs, testing) are welcome! See `CONTRIBUTING.md` for details.

---

## License
Distributed under the **MIT License**. See `LICENSE` for more information.

---

> © 2025 Giap Nguyen — *Built for learning, shared with ❤️.*
