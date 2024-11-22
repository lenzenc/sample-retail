from fastapi import FastAPI, HTTPException, Query, Depends, Response
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
import sqlite3
import yaml
from typing import List, Optional
from models import *
from database import get_db, lifespan

app = FastAPI(lifespan=lifespan)

# Items endpoints
@app.get("/items", response_model=PaginatedResponse[Item])
async def get_items(
    is_active: bool = True,
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    db: sqlite3.Connection = Depends(get_db)
):
    offset = (page - 1) * per_page
    total = db.execute(
        "SELECT COUNT(*) FROM items WHERE is_active = ?",
        (is_active,)
    ).fetchone()[0]

    cursor = db.execute(
        "SELECT * FROM items WHERE is_active = ? LIMIT ? OFFSET ?",
        (is_active, per_page, offset)
    )
    items = [dict(row) for row in cursor.fetchall()]
    return {
        "items": items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page
    }

@app.post("/items", response_model=Item)
async def create_item(
    item: ItemCreate,
    db: sqlite3.Connection = Depends(get_db)
):
    cursor = db.execute(
        """
        INSERT INTO items (title, description, barcode, price, is_active)
        VALUES (?, ?, ?, ?, ?)
        """,
        (item.title, item.description, item.barcode, item.price, item.is_active)
    )
    db.commit()
    
    created_item = db.execute(
        "SELECT * FROM items WHERE id = ?",
        (cursor.lastrowid,)
    ).fetchone()
    
    return dict(created_item)

@app.get("/items/{item_id}", response_model=Item)
async def get_item(
    item_id: int,
    db: sqlite3.Connection = Depends(get_db)
):
    item = db.execute(
        "SELECT * FROM items WHERE id = ?",
        (item_id,)
    ).fetchone()
    
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    
    return dict(item)

@app.put("/items/{item_id}", response_model=Item)
async def update_item(
    item_id: int,
    item: ItemCreate,
    db: sqlite3.Connection = Depends(get_db)
):
    cursor = db.execute(
        """
        UPDATE items 
        SET title = ?, description = ?, barcode = ?, price = ?, 
            is_active = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (item.title, item.description, item.barcode, item.price, 
         item.is_active, item_id)
    )
    db.commit()
    
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Item not found")
    
    updated_item = db.execute(
        "SELECT * FROM items WHERE id = ?",
        (item_id,)
    ).fetchone()
    
    return dict(updated_item)

@app.delete("/items/{item_id}")
async def delete_item(
    item_id: int,
    db: sqlite3.Connection = Depends(get_db)
):
    cursor = db.execute("DELETE FROM items WHERE id = ?", (item_id,))
    db.commit()
    
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Item not found")
    
    return {"message": "Item deleted successfully"}

# Orders endpoints
@app.get("/orders", response_model=PaginatedResponse[Order])
async def get_orders(
    status: Optional[OrderStatus] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    db: sqlite3.Connection = Depends(get_db)
):
    offset = (page - 1) * per_page
    if status:
        total = db.execute(
            "SELECT COUNT(*) FROM orders WHERE status = ?",
            (status.value,)
        ).fetchone()[0]
    else:
        total = db.execute("SELECT COUNT(*) FROM orders").fetchone()[0]    

    if status:
        cursor = db.execute(
            """
            SELECT * FROM orders 
            WHERE status = ? 
            LIMIT ? OFFSET ?
            """,
            (status.value, per_page, offset)
        )
    else:
        cursor = db.execute(
            "SELECT * FROM orders LIMIT ? OFFSET ?",
            (per_page, offset)
        )
    
    orders = []
    for order_row in cursor.fetchall():
        order_dict = dict(order_row)
        
        # Get order items
        items_cursor = db.execute(
            "SELECT * FROM order_items WHERE order_id = ?",
            (order_dict['id'],)
        )
        order_dict['order_items'] = [dict(item) for item in items_cursor.fetchall()]
        
        orders.append(order_dict)
    
    return {
        "items": orders,
        "total": total, 
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page
    }

@app.post("/orders", response_model=Order)
async def create_order(
    order: OrderCreate,
    db: sqlite3.Connection = Depends(get_db)
):
    # Insert order
    cursor = db.execute(
        """
        INSERT INTO orders (customer_id, picked_key_id, order_number, total_amount)
        VALUES (?, ?, ?, 0)
        """,
        (order.customer_id, order.picked_key_id, order.order_number)
    )
    order_id = cursor.lastrowid
    
    # Insert order items and calculate total
    total_amount = 0
    for item in order.order_items:
        db.execute(
            """
            INSERT INTO order_items (order_id, item_id, quantity, unit_price, subtotal)
            VALUES (?, ?, ?, ?, ?)
            """,
            (order_id, item.item_id, item.quantity, item.unit_price, item.subtotal)
        )
        total_amount += item.subtotal
    
    # Update order total
    db.execute(
        "UPDATE orders SET total_amount = ? WHERE id = ?",
        (total_amount, order_id)
    )
    db.commit()
    
    # Return created order
    created_order = db.execute(
        "SELECT * FROM orders WHERE id = ?",
        (order_id,)
    ).fetchone()
    
    return dict(created_order)

@app.get("/orders/{order_id}", response_model=Order)
async def get_order(
    order_id: int,
    db: sqlite3.Connection = Depends(get_db)
):
    order = db.execute(
        "SELECT * FROM orders WHERE id = ?",
        (order_id,)
    ).fetchone()
    
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    
    order_dict = dict(order)
    
    # Get order items
    items_cursor = db.execute(
        "SELECT * FROM order_items WHERE order_id = ?",
        (order_id,)
    )
    order_dict['order_items'] = [dict(item) for item in items_cursor.fetchall()]
    
    return order_dict

@app.put("/orders/{order_id}/status")
async def update_order_status(
    order_id: int,
    status: OrderStatus,
    db: sqlite3.Connection = Depends(get_db)
):
    cursor = db.execute(
        """
        UPDATE orders 
        SET status = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (status.value, order_id)
    )
    db.commit()
    
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Order not found")
    
    return {"message": "Order status updated successfully"}

# @app.get("/docs", include_in_schema=False)
# async def custom_swagger_ui_html():
#     return get_swagger_ui_html(
#         openapi_url="/openapi.yaml",
#         title="API Docs"
#     )

@app.get("/openapi.yaml", include_in_schema=False)
async def get_openapi_yaml():
    return Response(
        yaml.dump(app.openapi()),
        media_type="text/yaml"
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)