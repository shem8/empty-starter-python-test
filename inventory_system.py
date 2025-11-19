"""
E-commerce Inventory Management System
This system manages products, orders, and inventory for an online store.
"""

from datetime import datetime
import json


class Product:
    def __init__(self, product_id, name, price, category, stock_quantity):
        self.product_id = product_id
        self.name = name
        self.price = price
        self.category = category
        self.stock_quantity = stock_quantity
        self.created_at = datetime.now()
    
    def update_stock(self, quantity):
        if self.stock_quantity + quantity < 0:
            raise ValueError("Insufficient stock")
        self.stock_quantity += quantity
        return self.stock_quantity
    
    def apply_discount(self, percentage):
        if percentage < 0 or percentage > 100:
            raise ValueError("Invalid discount percentage")
        self.price = self.price * (1 - percentage / 100)
        return self.price
    
    def to_dict(self):
        return {
            "product_id": self.product_id,
            "name": self.name,
            "price": self.price,
            "category": self.category,
            "stock_quantity": self.stock_quantity,
            "created_at": self.created_at.isoformat()
        }


class OrderItem:
    def __init__(self, product_id, quantity, unit_price):
        self.product_id = product_id
        self.quantity = quantity
        self.unit_price = unit_price
    
    def get_total_price(self):
        return self.quantity * self.unit_price


class Customer:
    def __init__(self, customer_id, name, email, phone=None, address=None):
        self.customer_id = customer_id
        self.name = name
        self.email = email
        self.phone = phone
        self.address = address
    
    def get_contact_info(self):
        contact = {"email": self.email}
        if self.phone:
            contact["phone"] = self.phone
        if self.address:
            contact["address"] = self.address
        return contact


class Order:
    def __init__(self, order_id, customer, items):
        self.order_id = order_id
        self.customer = customer
        self.items = items
        self.created_at = datetime.now()
        self.status = "pending"
    
    def calculate_total(self):
        return sum(item.get_total_price() for item in self.items)
    
    def add_item(self, item):
        self.items.append(item)
    
    def update_status(self, new_status):
        valid_statuses = ["pending", "confirmed", "shipped", "delivered", "cancelled"]
        if new_status not in valid_statuses:
            raise ValueError(f"Invalid status. Must be one of: {valid_statuses}")
        self.status = new_status


class InventoryManager:
    def __init__(self):
        self.products = {}
        self.orders = {}
        self.customers = {}
    
    def add_product(self, product):
        if product.product_id in self.products:
            raise ValueError("Product already exists")
        self.products[product.product_id] = product
        return product
    
    def get_product(self, product_id):
        return self.products.get(product_id)
    
    def update_product_stock(self, product_id, quantity_change):
        product = self.get_product(product_id)
        if not product:
            raise ValueError("Product not found")
        return product.update_stock(quantity_change)
    
    def search_products(self, category=None, min_price=None, max_price=None):
        results = []
        for product in self.products.values():
            if category and product.category != category:
                continue
            if min_price and product.price < min_price:
                continue
            if max_price and product.price > max_price:
                continue
            results.append(product)
        return results
    
    def get_low_stock_products(self, threshold=10):
        return [p for p in self.products.values() if p.stock_quantity <= threshold]
    
    def create_order(self, customer_id, items_data):
        customer = self.customers.get(customer_id)
        if not customer:
            raise ValueError("Customer not found")
        
        order_items = []
        for item_data in items_data:
            product = self.get_product(item_data["product_id"])
            if not product:
                raise ValueError(f"Product {item_data['product_id']} not found")
            
            if product.stock_quantity < item_data["quantity"]:
                raise ValueError(f"Insufficient stock for {product.name}")
            
            order_item = OrderItem(
                product_id=product.product_id,
                quantity=item_data["quantity"],
                unit_price=product.price
            )
            order_items.append(order_item)
        
        order_id = f"ORD-{len(self.orders) + 1:06d}"
        order = Order(order_id, customer, order_items)
        self.orders[order_id] = order
        
        # Update stock quantities
        for item in order_items:
            self.update_product_stock(item.product_id, -item.quantity)
        
        return order
    
    def add_customer(self, customer):
        self.customers[customer.customer_id] = customer
        return customer
    
    def generate_inventory_report(self):
        total_products = len(self.products)
        total_value = sum(p.price * p.stock_quantity for p in self.products.values())
        low_stock = self.get_low_stock_products()
        
        return {
            "total_products": total_products,
            "total_inventory_value": total_value,
            "low_stock_count": len(low_stock),
            "low_stock_products": [p.name for p in low_stock]
        }


class SalesAnalytics:
    def __init__(self, inventory_manager):
        self.inventory = inventory_manager
    
    def calculate_revenue(self, start_date=None, end_date=None):
        total = 0
        for order in self.inventory.orders.values():
            if start_date and order.created_at < start_date:
                continue
            if end_date and order.created_at > end_date:
                continue
            if order.status in ["confirmed", "shipped", "delivered"]:
                total += order.calculate_total()
        return total
    
    def get_top_selling_products(self, limit=10):
        product_sales = {}
        
        for order in self.inventory.orders.values():
            if order.status in ["confirmed", "shipped", "delivered"]:
                for item in order.items:
                    if item.product_id in product_sales:
                        product_sales[item.product_id] += item.quantity
                    else:
                        product_sales[item.product_id] = item.quantity
        
        # Sort by quantity sold
        sorted_products = sorted(product_sales.items(), key=lambda x: x[1], reverse=True)
        
        result = []
        for product_id, quantity in sorted_products[:limit]:
            product = self.inventory.get_product(product_id)
            if product:
                result.append({
                    "product_id": product_id,
                    "name": product.name,
                    "quantity_sold": quantity
                })
        
        return result
    
    def get_customer_analytics(self, customer_id):
        customer = self.inventory.customers.get(customer_id)
        if not customer:
            return None
        
        customer_orders = [o for o in self.inventory.orders.values() if o.customer.customer_id == customer_id]
        total_spent = sum(o.calculate_total() for o in customer_orders if o.status != "cancelled")
        order_count = len(customer_orders)
        
        return {
            "customer_name": customer.name,
            "total_orders": order_count,
            "total_spent": total_spent,
            "average_order_value": total_spent / order_count if order_count > 0 else 0
        }


if __name__ == "__main__":
    inventory = InventoryManager()
    analytics = SalesAnalytics(inventory)
    
    products = [
        Product("LAPTOP001", "Gaming Laptop", 1299.99, "Electronics", 15),
        Product("MOUSE001", "Wireless Mouse", 29.99, "Electronics", 50),
        Product("BOOK001", "Python Programming", 49.99, "Books", 25)
    ]
    
    for product in products:
        inventory.add_product(product)
    
    customers = [
        Customer("CUST001", "Alice Johnson", "alice@example.com", "+1234567890"),
        Customer("CUST002", "Bob Smith", "bob@example.com")
    ]
    
    for customer in customers:
        inventory.add_customer(customer)
    
    order1 = inventory.create_order("CUST001", [
        {"product_id": "LAPTOP001", "quantity": 1},
        {"product_id": "MOUSE001", "quantity": 2}
    ])
    
    order1.update_status("confirmed")
    
    report = inventory.generate_inventory_report()
    print("Inventory Report:", json.dumps(report, indent=2))
    
    top_products = analytics.get_top_selling_products(5)
    print("Top Selling Products:", json.dumps(top_products, indent=2))
    
    customer_stats = analytics.get_customer_analytics("CUST001")
    print("Customer Analytics:", json.dumps(customer_stats, indent=2))
