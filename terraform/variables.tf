variable "gcp_project_id" {
  type        = string
  description = "The ID of the Google Cloud project"
}

variable "gcp_region" {
  type        = string
  description = "The region for Google Cloud resources"
  default     = "us-central1"
}

variable "firestore_location" {
  type        = string
  description = "The location for Firestore database"
  default     = "us-central1"
}

variable "server_image_tag" {
  type        = string
  description = "The Docker image tag for the Blumelein Server"
}

variable "environment" {
  type        = string
  description = "Environment name (development, staging, production)"
  default     = "production"
}

variable "stripe_api_key" {
  type        = string
  description = "Stripe API secret key"
  sensitive   = true
}

variable "stripe_publishable_key" {
  type        = string
  description = "Stripe publishable key"
  sensitive   = true
}

variable "stripe_webhook_secret" {
  type        = string
  description = "Stripe webhook secret"
  sensitive   = true
}

variable "admin_api_key" {
  type        = string
  description = "Admin API key for management endpoints"
  sensitive   = true
}

variable "allowed_origins" {
  type        = string
  description = "Comma-separated list of allowed CORS origins"
  default     = "https://yourdomain.com"
}

variable "service_name" {
  type        = string
  description = "Name of the Cloud Run service"
  default     = "blumelein-server"
}

variable "min_instances" {
  type        = number
  description = "Minimum number of instances"
  default     = 0
}

variable "max_instances" {
  type        = number
  description = "Maximum number of instances"
  default     = 10
}

variable "memory_limit" {
  type        = string
  description = "Memory limit for the Cloud Run service"
  default     = "512Mi"
}

variable "cpu_limit" {
  type        = string
  description = "CPU limit for the Cloud Run service"
  default     = "1000m"
}

