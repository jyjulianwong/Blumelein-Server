# Google Cloud Firestore Database
# NOTE: Firestore database should be created manually or imported if it already exists

resource "google_firestore_database" "main" {
  project     = var.gcp_project_id
  name        = "(default)"
  location_id = var.firestore_location
  type        = "FIRESTORE_NATIVE"

  # Prevent accidental deletion
  delete_protection_state = "DELETE_PROTECTION_ENABLED"

  depends_on = [google_project_service.firestore_api]
}

# Firestore Collections
# NOTE: Collections in Firestore are created automatically when documents are added
# The application will create these collections:
# - orders: Stores all flower shop orders with items, buyer info, payment status, etc.
#
# Document structure for orders collection:
# {
#   order_id: string (UUID),
#   items: array of {
#     item_id: string (UUID),
#     main_colours: array of strings,
#     size: string ("S", "M", "L"),
#     comments: string (optional),
#     created_at: timestamp
#   },
#   buyer_full_name: string,
#   delivery_address: string,
#   payment_status: string ("Incomplete", "Completed"),
#   order_status: string ("Not Started", "In Progress", "Completed"),
#   created_at: timestamp,
#   updated_at: timestamp
# }

