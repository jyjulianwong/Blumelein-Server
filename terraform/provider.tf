terraform {
  required_version = ">= 1.7.0"
  
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
  }

  backend "gcs" {
    # Backend configuration will be provided via -backend-config flags
    # bucket = "your-terraform-state-bucket"
    # prefix = "terraform/state"
  }
}

provider "google" {
  project = var.gcp_project_id
  region  = var.gcp_region
}

