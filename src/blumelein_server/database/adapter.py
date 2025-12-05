"""Abstract database adapter interface."""

from abc import ABC, abstractmethod
from uuid import UUID

from ..models.schemas import Order, PaymentStatus, OrderStatus


class DatabaseAdapter(ABC):
    """
    Abstract base class for database operations.
    
    This interface defines all database operations required by the application.
    Different implementations (Firestore, PostgreSQL, etc.) can be created
    by extending this class.
    """

    @abstractmethod
    async def create_order(self, order: Order) -> Order:
        """
        Store a new order in the database.
        
        Args:
            order: Order object to store
            
        Returns:
            The created order
        """
        pass

    @abstractmethod
    async def get_order(self, order_id: UUID) -> Order | None:
        """
        Retrieve an order by ID.
        
        Args:
            order_id: Unique order identifier
            
        Returns:
            Order if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_all_orders(self) -> list[Order]:
        """
        Retrieve all orders.
        
        Returns:
            List of all orders
        """
        pass

    @abstractmethod
    async def update_order_payment_status(
        self,
        order_id: UUID,
        payment_status: PaymentStatus
    ) -> Order | None:
        """
        Update the payment status of an order.
        
        Args:
            order_id: Order to update
            payment_status: New payment status
            
        Returns:
            Updated order if found, None otherwise
        """
        pass

    @abstractmethod
    async def update_order_status(
        self,
        order_id: UUID,
        order_status: OrderStatus
    ) -> Order | None:
        """
        Update the processing status of an order.
        
        Args:
            order_id: Order to update
            order_status: New order status
            
        Returns:
            Updated order if found, None otherwise
        """
        pass

    @abstractmethod
    async def initialize(self) -> None:
        """
        Initialize the database connection and any required setup.
        Called during application startup.
        """
        pass

    @abstractmethod
    async def close(self) -> None:
        """
        Close database connections and cleanup resources.
        Called during application shutdown.
        """
        pass

