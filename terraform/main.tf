# Enable required APIs
resource "google_project_service" "run_api" {
  service            = "run.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "firestore_api" {
  service            = "firestore.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "artifactregistry_api" {
  service            = "artifactregistry.googleapis.com"
  disable_on_destroy = false
}

# Artifact Registry for Docker images
resource "google_artifact_registry_repository" "docker" {
  location      = var.gcp_region
  repository_id = "blumelein-docker"
  description   = "Docker repository for Blumelein Server"
  format        = "DOCKER"

  depends_on = [google_project_service.artifactregistry_api]
}

# Cloud Run Service
resource "google_cloud_run_service" "server" {
  name     = var.service_name
  location = var.gcp_region

  template {
    metadata {
      annotations = {
        "autoscaling.knative.dev/minScale" = var.min_instances
        "autoscaling.knative.dev/maxScale" = var.max_instances
        "run.googleapis.com/client-name"   = "terraform"
      }
    }

    spec {
      service_account_name = google_service_account.cloudrun.email
      
      containers {
        image = var.server_image_tag

        ports {
          container_port = 8000
        }

        resources {
          limits = {
            memory = var.memory_limit
            cpu    = var.cpu_limit
          }
        }

        # Environment variables
        env {
          name  = "ENVIRONMENT"
          value = var.environment
        }

        env {
          name  = "DATABASE_TYPE"
          value = "firestore"
        }

        env {
          name  = "GOOGLE_CLOUD_PROJECT"
          value = var.gcp_project_id
        }

        env {
          name  = "GOOGLE_CLOUD_LOCATION"
          value = var.firestore_location
        }

        env {
          name  = "STRIPE_API_KEY"
          value = var.stripe_api_key
        }

        env {
          name  = "STRIPE_PUBLISHABLE_KEY"
          value = var.stripe_publishable_key
        }

        env {
          name  = "STRIPE_WEBHOOK_SECRET"
          value = var.stripe_webhook_secret
        }

        env {
          name  = "ADMIN_API_KEY"
          value = var.admin_api_key
        }

        env {
          name  = "ALLOWED_ORIGINS"
          value = var.allowed_origins
        }

        env {
          name  = "API_HOST"
          value = "0.0.0.0"
        }

        env {
          name  = "API_PORT"
          value = "8000"
        }
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }

  depends_on = [google_project_service.run_api]
}

# Allow public access to Cloud Run service
resource "google_cloud_run_service_iam_member" "server_public" {
  service  = google_cloud_run_service.server.name
  location = google_cloud_run_service.server.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Service Account for Cloud Run
resource "google_service_account" "cloudrun" {
  account_id   = "${var.service_name}-sa"
  display_name = "Service Account for ${var.service_name}"
  description  = "Used by Cloud Run service to access Google Cloud resources"
}

# Grant Firestore access to service account
resource "google_project_iam_member" "cloudrun_firestore" {
  project = var.gcp_project_id
  role    = "roles/datastore.user"
  member  = "serviceAccount:${google_service_account.cloudrun.email}"
}

# Grant logging access to service account
resource "google_project_iam_member" "cloudrun_logging" {
  project = var.gcp_project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.cloudrun.email}"
}

# Outputs
output "service_url" {
  description = "URL of the deployed Cloud Run service"
  value       = google_cloud_run_service.server.status[0].url
}

output "service_account_email" {
  description = "Email of the Cloud Run service account"
  value       = google_service_account.cloudrun.email
}

output "artifact_registry_url" {
  description = "URL of the Artifact Registry repository"
  value       = "${var.gcp_region}-docker.pkg.dev/${var.gcp_project_id}/${google_artifact_registry_repository.docker.repository_id}"
}

