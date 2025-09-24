from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import json

app = FastAPI(title="RestaurantIA Backend")

# Configuración de PostgreSQL
# ⚠️ ¡REEMPLAZA 'tu_contraseña' con tu contraseña real de PostgreSQL!
DATABASE_URL = "dbname=restaurant_db user=postgres password=postgres host=localhost port=5432"

def get_db():
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    try:
        yield conn
    finally:
        conn.close()

# Modelos
class ItemMenu(BaseModel):
    nombre: str
    precio: float
    tipo: str

class PedidoCreate(BaseModel):
    mesa_numero: int
    items: List[dict]
    estado: str = "Pendiente"

class PedidoResponse(BaseModel):
    id: int
    mesa_numero: int
    items: List[dict]
    estado: str
    fecha_hora: str
    numero_app: Optional[int] = None

# Endpoints
@app.get("/health")
def health():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        conn.close()
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        return {"status": "error", "database": str(e)}

@app.get("/menu/items", response_model=List[ItemMenu])
def obtener_menu(conn: psycopg2.extensions.connection = Depends(get_db)):
    with conn.cursor() as cursor:
        cursor.execute("SELECT nombre, precio, tipo FROM menu ORDER BY tipo, nombre")
        items = cursor.fetchall()
        return items

@app.post("/pedidos", response_model=PedidoResponse)
def crear_pedido(pedido: PedidoCreate, conn: psycopg2.extensions.connection = Depends(get_db)):
    with conn.cursor() as cursor:
        numero_app = None
        if pedido.mesa_numero == 99:
            cursor.execute("SELECT MAX(numero_app) FROM pedidos WHERE mesa_numero = 99")
            max_app = cursor.fetchone()['max'] or 0
            numero_app = max_app + 1

        fecha_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        cursor.execute("""
            INSERT INTO pedidos (mesa_numero, numero_app, estado, fecha_hora, items)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id, mesa_numero, numero_app, estado, fecha_hora, items
        """, (
            pedido.mesa_numero,
            numero_app,
            pedido.estado,
            fecha_hora,
            json.dumps(pedido.items)
        ))
        
        result = cursor.fetchone()
        conn.commit()
        
        return {
            "id": result['id'],
            "mesa_numero": result['mesa_numero'],
            "items": json.loads(result['items']),
            "estado": result['estado'],
            "fecha_hora": result['fecha_hora'].strftime("%Y-%m-%d %H:%M:%S") if isinstance(result['fecha_hora'], datetime) else result['fecha_hora'],
            "numero_app": result['numero_app']
        }

@app.get("/pedidos/activos", response_model=List[PedidoResponse])
def obtener_pedidos_activos(conn: psycopg2.extensions.connection = Depends(get_db)):
    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT id, mesa_numero, numero_app, estado, fecha_hora, items 
            FROM pedidos 
            WHERE estado IN ('Pendiente', 'En preparacion', 'Listo')
            ORDER BY fecha_hora DESC
        """)
        pedidos = []
        for row in cursor.fetchall():
            pedidos.append({
                "id": row['id'],
                "mesa_numero": row['mesa_numero'],
                "numero_app": row['numero_app'],
                "estado": row['estado'],
                "fecha_hora": row['fecha_hora'].strftime("%Y-%m-%d %H:%M:%S") if isinstance(row['fecha_hora'], datetime) else row['fecha_hora'],
                "items": json.loads(row['items']) if isinstance(row['items'], str) else row['items']
            })
        return pedidos

@app.patch("/pedidos/{pedido_id}/estado")
def actualizar_estado_pedido(pedido_id: int, estado: str, conn: psycopg2.extensions.connection = Depends(get_db)):
    if estado not in ["Pendiente", "En preparacion", "Listo", "Entregado"]:
        raise HTTPException(status_code=400, detail="Estado inválido")
    
    with conn.cursor() as cursor:
        cursor.execute(
            "UPDATE pedidos SET estado = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
            (estado, pedido_id)
        )
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Pedido no encontrado")
        conn.commit()
        return {"status": "ok"}

@app.get("/mesas")
def obtener_mesas(conn: psycopg2.extensions.connection = Depends(get_db)):
    """
    Obtiene el estado real de todas las mesas desde la base de datos.
    """
    try:
        with conn.cursor() as cursor:
            # Obtener mesas físicas y su estado de ocupación
            cursor.execute("""
                SELECT m.numero, m.capacidad,
                       CASE 
                           WHEN p.mesa_numero IS NOT NULL THEN true 
                           ELSE false 
                       END as ocupada
                FROM (
                    SELECT 1 as numero, 2 as capacidad
                    UNION SELECT 2, 2
                    UNION SELECT 3, 4  
                    UNION SELECT 4, 4
                    UNION SELECT 5, 6
                    UNION SELECT 6, 6
                ) as m
                LEFT JOIN pedidos p ON m.numero = p.mesa_numero 
                    AND p.estado IN ('Pendiente', 'En preparacion', 'Listo')
                ORDER BY m.numero
            """)
            
            mesas = []
            for row in cursor.fetchall():
                mesas.append({
                    "numero": row[0],
                    "capacidad": row[1],
                    "ocupada": row[2]
                })
            
            # Agregar mesa virtual
            mesas.append({
                "numero": 99,
                "capacidad": 1,
                "ocupada": False,
                "es_virtual": True
            })
            
            return mesas
            
    except Exception as e:
        # En caso de error, devolver mesas por defecto
        return [
            {"numero": 1, "capacidad": 2, "ocupada": False},
            {"numero": 2, "capacidad": 2, "ocupada": False},
            {"numero": 3, "capacidad": 4, "ocupada": False},
            {"numero": 4, "capacidad": 4, "ocupada": False},
            {"numero": 5, "capacidad": 6, "ocupada": False},
            {"numero": 6, "capacidad": 6, "ocupada": False},
            {"numero": 99, "capacidad": 1, "ocupada": False, "es_virtual": True}
        ]

# Endpoint para inicializar menú (ejecutar solo una vez)
@app.post("/menu/inicializar")
def inicializar_menu(conn: psycopg2.extensions.connection = Depends(get_db)):
    menu_inicial = [
        # Entradas
        ("Empanada Kunai", 70.00, "Entradas"),
        ("Dedos de queso (5pz)", 75.00, "Entradas"),
        ("Chile Relleno", 60.00, "Entradas"),
        # Platillos
        ("Camarones roca", 160.00, "Platillos"),
        ("Teriyaki", 130.00, "Platillos"),
        ("Bonneles (300gr)", 150.00, "Platillos"),
        # Arroces
        ("Yakimeshi Especial", 150.00, "Arroces"),
        ("Yakimeshi Kunai", 140.00, "Arroces"),
        ("Gohan Mixto", 125.00, "Arroces"),
        # Naturales
        ("California Roll", 100.00, "Naturales"),
        ("Tuna Roll", 130.00, "Naturales"),
        ("Kanisweet", 120.00, "Naturales"),
        # Empanizados
        ("Mar y Tierra", 95.00, "Empanizados"),
        ("Cordon Blue", 105.00, "Empanizados"),
        ("Caribe Roll", 115.00, "Empanizados"),
        # Gratinados
        ("Kunai Especial", 150.00, "Gratinados"),
        ("Chuma Roll", 145.00, "Gratinados"),
        ("Ninja Roll", 135.00, "Gratinados"),
        # Kunai Kids
        ("Baby Roll (8pz)", 60.00, "Kunai Kids"),
        ("Chicken Sweet (7pz)", 60.00, "Kunai Kids"),
        ("Chesse Puffs (10pz)", 55.00, "Kunai Kids"),
        # Bebidas
        ("Te refil", 35.00, "Bebidas"),
        ("Coca-cola", 35.00, "Bebidas"),
        ("Agua natural", 20.00, "Bebidas"),
        # Extras
        ("Camaron", 20.00, "Extras"),
        ("Aguacate", 25.00, "Extras"),
        ("Siracha", 10.00, "Extras"),
    ]
    
    with conn.cursor() as cursor:
        for nombre, precio, tipo in menu_inicial:
            cursor.execute("""
                INSERT INTO menu (nombre, precio, tipo)
                VALUES (%s, %s, %s)
                ON CONFLICT (nombre, tipo) DO NOTHING
            """, (nombre, precio, tipo))
        conn.commit()
        return {"status": "ok", "items_insertados": len(menu_inicial)}

# ¡NUEVO ENDPOINT! → Eliminar último ítem de un pedido
@app.delete("/pedidos/{pedido_id}/ultimo_item")
def eliminar_ultimo_item(pedido_id: int, conn: psycopg2.extensions.connection = Depends(get_db)):
    with conn.cursor() as cursor:
        # Obtener items actuales
        cursor.execute("SELECT items FROM pedidos WHERE id = %s", (pedido_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Pedido no encontrado")
        
        items = json.loads(row['items'])
        if not items:
            raise HTTPException(status_code=400, detail="No hay ítems para eliminar")
        
        # Eliminar último ítem
        items.pop()
        
        # Actualizar en base de datos
        cursor.execute("UPDATE pedidos SET items = %s WHERE id = %s", (json.dumps(items), pedido_id))
        conn.commit()
        return {"status": "ok"}
    
@app.put("/pedidos/{pedido_id}")
def actualizar_pedido(pedido_id: int, pedido_actualizado: PedidoCreate, conn: psycopg2.extensions.connection = Depends(get_db)):
    """
    Actualiza completamente un pedido (ítems, estado, etc.)
    """
    with conn.cursor() as cursor:
        # Verificar que el pedido exista
        cursor.execute("SELECT id FROM pedidos WHERE id = %s", (pedido_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Pedido no encontrado")
        
        # Actualizar el pedido
        fecha_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            UPDATE pedidos 
            SET mesa_numero = %s, estado = %s, fecha_hora = %s, items = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (
            pedido_actualizado.mesa_numero,
            pedido_actualizado.estado,
            fecha_hora,
            json.dumps(pedido_actualizado.items),
            pedido_id
        ))
        conn.commit()
        return {"status": "ok", "message": "Pedido actualizado"}

@app.delete("/pedidos/{pedido_id}")
def eliminar_pedido(pedido_id: int, conn: psycopg2.extensions.connection = Depends(get_db)):
    """
    Elimina un pedido completamente del sistema
    """
    with conn.cursor() as cursor:
        cursor.execute("DELETE FROM pedidos WHERE id = %s", (pedido_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Pedido no encontrado")
        conn.commit()
        return {"status": "ok", "message": "Pedido eliminado"}

@app.post("/menu/items")
def agregar_item_menu(item: ItemMenu, conn: psycopg2.extensions.connection = Depends(get_db)):
    """
    Agrega un nuevo ítem al menú
    """
    with conn.cursor() as cursor:
        cursor.execute("""
            INSERT INTO menu (nombre, precio, tipo)
            VALUES (%s, %s, %s)
            RETURNING id
        """, (item.nombre, item.precio, item.tipo))
        item_id = cursor.fetchone()['id']
        conn.commit()
        return {"status": "ok", "id": item_id, "message": "Ítem agregado al menú"}

@app.delete("/menu/items")
def eliminar_item_menu(nombre: str, tipo: str, conn: psycopg2.extensions.connection = Depends(get_db)):
    """
    Elimina un ítem del menú por nombre y tipo
    """
    with conn.cursor() as cursor:
        cursor.execute("DELETE FROM menu WHERE nombre = %s AND tipo = %s", (nombre, tipo))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Ítem no encontrado en el menú")
        conn.commit()
        return {"status": "ok", "message": "Ítem eliminado del menú"}