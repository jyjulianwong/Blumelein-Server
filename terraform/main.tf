# Enable required APIs
resource "google_project_service" "run_api" {
  service            = "run.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "firestore_api" {
  service            = "firestore.googleapis.com"
  disable_on_destroy = false
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
      service_account_name = "${var.service_name}-sa@${var.gcp_project_id}.iam.gserviceaccount.com"
      
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

# Service account is expected to be pre-created manually
# Service account email format: ${var.service_name}-sa@${var.gcp_project_id}.iam.gserviceaccount.com
# 
# Required IAM roles for the service account:
# - roles/datastore.user (Firestore access)
# - roles/logging.logWriter (Cloud Logging access)

# Outputs
output "service_url" {
  description = "URL of the deployed Cloud Run service"
  value       = google_cloud_run_service.server.status[0].url
}

output "service_account_email" {
  description = "Email of the Cloud Run service account"
  value       = "${var.service_name}-sa@${var.gcp_project_id}.iam.gserviceaccount.com"
}

