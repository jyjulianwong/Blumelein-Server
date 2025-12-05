"""Firestore database adapter implementation."""

from datetime import datetime
from uuid import UUID

from google.cloud import firestore
from google.cloud.firestore_v1.base_query import FieldFilter

from ..models.schemas import Order, PaymentStatus, OrderStatus, Item
from .adapter import DatabaseAdapter


class FirestoreAdapter(DatabaseAdapter):
    """
    Firestore implementation of the database adapter.
    
    This adapter uses Google Cloud Firestore as the backend database.
    Orders are stored in a 'orders' collection with the order_id as the document ID.
    """

    def __init__(self, project_id: str | None = None):
        """
        Initialize Firestore adapter.
        
        Args:
            project_id: Google Cloud project ID. If None, uses default credentials.
        """
        self.project_id = project_id
        self.db: firestore.AsyncClient | None = None
        self.orders_collection = "orders"

    async def initialize(self) -> None:
        """Initialize Firestore client."""
        if self.project_id:
            self.db = firestore.AsyncClient(project=self.project_id)
        else:
            self.db = firestore.AsyncClient()
        print(f"📊 Firestore initialized (project: {self.project_id or 'default'})")

    async def close(self) -> None:
        """Close Firestore client."""
        if self.db:
            self.db.close()
            print("📊 Firestore connection closed")

    def _order_to_dict(self, order: Order) -> dict:
        """
        Convert Order object to Firestore-compatible dictionary.
        
        Args:
            order: Order object to convert
            
        Returns:
            Dictionary representation
        """
        return {
            "order_id": str(order.order_id),
            "items": [
                {
                    "item_id": str(item.item_id),
                    "main_colours": item.main_colours,
                    "size": item.size.value,
                    "comments": item.comments,
                    "created_at": item.created_at,
                }
                for item in order.items
            ],
            "buyer_full_name": order.buyer_full_name,
            "delivery_address": order.delivery_address,
            "payment_status": order.payment_status.value,
            "order_status": order.order_status.value,
            "created_at": order.created_at,
            "updated_at": order.updated_at,
        }

    def _dict_to_order(self, data: dict) -> Order:
        """
        Convert Firestore dictionary to Order object.
        
        Args:
            data: Dictionary from Firestore
            
        Returns:
            Order object
        """
        items = [
            Item(
                item_id=UUID(item["item_id"]),
                main_colours=item["main_colours"],
                size=item["size"],
                comments=item.get("comments"),
                created_at=item["created_at"],
            )
            for item in data["items"]
        ]

        return Order(
            order_id=UUID(data["order_id"]),
            items=items,
            buyer_full_name=data["buyer_full_name"],
            delivery_address=data["delivery_address"],
            payment_status=PaymentStatus(data["payment_status"]),
            order_status=OrderStatus(data["order_status"]),
            created_at=data["created_at"],
            updated_at=data["updated_at"],
        )

    async def create_order(self, order: Order) -> Order:
        """Store a new order in Firestore."""
        if not self.db:
            raise RuntimeError("Database not initialized. Call initialize() first.")

        order_dict = self._order_to_dict(order)
        doc_ref = self.db.collection(self.orders_collection).document(str(order.order_id))
        await doc_ref.set(order_dict)
        
        return order

    async def get_order(self, order_id: UUID) -> Order | None:
        """Retrieve an order by ID from Firestore."""
        if not self.db:
            raise RuntimeError("Database not initialized. Call initialize() first.")

        doc_ref = self.db.collection(self.orders_collection).document(str(order_id))
        doc = await doc_ref.get()
        
        if not doc.exists:
            return None
        
        return self._dict_to_order(doc.to_dict())

    async def get_all_orders(self) -> list[Order]:
        """Retrieve all orders from Firestore."""
        if not self.db:
            raise RuntimeError("Database not initialized. Call initialize() first.")

        orders_ref = self.db.collection(self.orders_collection)
        docs = orders_ref.stream()
        
        orders = []
        async for doc in docs:
            orders.append(self._dict_to_order(doc.to_dict()))
        
        # Sort by created_at descending (newest first)
        orders.sort(key=lambda x: x.created_at, reverse=True)
        
        return orders

    async def update_order_payment_status(
        self,
        order_id: UUID,
        payment_status: PaymentStatus
    ) -> Order | None:
        """Update the payment status of an order in Firestore."""
        if not self.db:
            raise RuntimeError("Database not initialized. Call initialize() first.")

        doc_ref = self.db.collection(self.orders_collection).document(str(order_id))
        doc = await doc_ref.get()
        
        if not doc.exists:
            return None
        
        # Update payment status and updated_at timestamp
        await doc_ref.update({
            "payment_status": payment_status.value,
            "updated_at": datetime.utcnow(),
        })
        
        # Fetch and return updated order
        updated_doc = await doc_ref.get()
        return self._dict_to_order(updated_doc.to_dict())

    async def update_order_status(
        self,
        order_id: UUID,
        order_status: OrderStatus
    ) -> Order | None:
        """Update the processing status of an order in Firestore."""
        if not self.db:
            raise RuntimeError("Database not initialized. Call initialize() first.")

        doc_ref = self.db.collection(self.orders_collection).document(str(order_id))
        doc = await doc_ref.get()
        
        if not doc.exists:
            return None
        
        # Update order status and updated_at timestamp
        await doc_ref.update({
            "order_status": order_status.value,
            "updated_at": datetime.utcnow(),
        })
        
        # Fetch and return updated order
        updated_doc = await doc_ref.get()
        return self._dict_to_order(updated_doc.to_dict())

