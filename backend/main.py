"""
CartPay - Backend simulado
---------------------------
Simula:
- Base de datos de productos (código, nombre, precio, peso, pasillo)
- Carrito con celdas de carga simuladas (peso esperado vs peso real)
- Pago simulado (genera boleta + código QR de validación)
- Portal de salida con doble pesaje (valida que lo que se paga = lo que se lleva)

Cómo correrlo:
    cd cartpay/backend
    python -m venv venv
    venv\\Scripts\\activate      (Windows)  |  source venv/bin/activate (Mac/Linux)
    pip install -r requirements.txt
    uvicorn main:app --reload

Luego abrimos: http://127.0.0.1:8000/docs  (para probar la API)
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict
import random
import uuid
import time

app = FastAPI(title="CartPay API")

# Permite que el frontend (index.html) se conecte sin problemas de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# 1. BASE DE DATOS SIMULADA DE PRODUCTOS
# ---------------------------------------------------------------------------
# codigo = lo que "leería" el escáner QR / código de barras
PRODUCTOS: Dict[str, dict] = {
    "7801234560012": {"nombre": "Arroz Grado 1 1kg", "precio": 1590, "peso_kg": 1.0, "pasillo": "Pasillo 3 - Abarrotes"},
    "7801234560029": {"nombre": "Aceite Vegetal 900ml", "precio": 2390, "peso_kg": 0.9, "pasillo": "Pasillo 3 - Abarrotes"},
    "7801234560036": {"nombre": "Leche Entera 1L", "precio": 1090, "peso_kg": 1.03, "pasillo": "Pasillo 1 - Lácteos"},
    "7801234560043": {"nombre": "Pan de Molde", "precio": 1990, "peso_kg": 0.5, "pasillo": "Pasillo 2 - Panadería"},
    "7801234560050": {"nombre": "Detergente 3kg", "precio": 6490, "peso_kg": 3.0, "pasillo": "Pasillo 5 - Limpieza"},
    "7801234560067": {"nombre": "Bebida Cola 1.5L", "precio": 1590, "peso_kg": 1.55, "pasillo": "Pasillo 4 - Bebidas"},
    "7801234560074": {"nombre": "Manzanas x kg", "precio": 1290, "peso_kg": 1.0, "pasillo": "Pasillo 0 - Frutas y Verduras"},
    "7801234560081": {"nombre": "Papel Higiénico x4", "precio": 2790, "peso_kg": 0.6, "pasillo": "Pasillo 5 - Limpieza"},
}

# ---------------------------------------------------------------------------
# 2. "BASE DE DATOS" DE CARRITOS ACTIVOS (en memoria, simulación)
# ---------------------------------------------------------------------------
# En un proyecto real esto iría en una base de datos (SQLite/Postgres).
CARRITOS: Dict[str, dict] = {}


def nuevo_carrito_dict():
    return {
        "items": [],           # lista de productos escaneados
        "peso_esperado": 0.0,  # suma de pesos declarados en la BD
        "pagado": False,
        "total": 0,
        "boleta_qr": None,
    }


# ---------------------------------------------------------------------------
# 3. MODELOS DE DATOS (lo que la tablet envía/recibe)
# ---------------------------------------------------------------------------
class EscanearRequest(BaseModel):
    carrito_id: str
    codigo: str


class QuitarRequest(BaseModel):
    carrito_id: str
    codigo: str


class PagoRequest(BaseModel):
    carrito_id: str
    metodo: str  # "tarjeta" o "celular"


class SalidaRequest(BaseModel):
    carrito_id: str


# ---------------------------------------------------------------------------
# 4. SIMULADOR DE CELDAS DE CARGA
# ---------------------------------------------------------------------------
def leer_celdas_de_carga(peso_esperado: float) -> float:
    """
    Simula la lectura de las 4 celdas de carga del carrito.
    En la vida real, esto leería un sensor HX711 conectado a las celdas.
    Aquí generamos un peso "real" con un pequeño error aleatorio (ruido de sensor),
    igual que pasaría con hardware real.
    """
    ruido = random.uniform(-0.05, 0.05)  # +-50 gramos de margen de error del sensor
    return round(peso_esperado + ruido, 3)


# ---------------------------------------------------------------------------
# 5. ENDPOINTS
# ---------------------------------------------------------------------------

@app.post("/carrito/nuevo")
def crear_carrito():
    """Se llama cuando el cliente retira un carrito y lo activa en la tablet."""
    carrito_id = str(uuid.uuid4())[:8]
    CARRITOS[carrito_id] = nuevo_carrito_dict()
    return {"carrito_id": carrito_id}


@app.get("/productos/{codigo}")
def buscar_producto(codigo: str):
    """Consulta de precio / ubicación al buscar un producto (sin agregarlo aún)."""
    producto = PRODUCTOS.get(codigo)
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return producto


@app.get("/productos")
def listar_productos(q: str = ""):
    """Buscador de productos por nombre (para la barra de búsqueda de la tablet)."""
    resultados = []
    for codigo, p in PRODUCTOS.items():
        if q.lower() in p["nombre"].lower():
            resultados.append({"codigo": codigo, **p})
    return resultados


@app.post("/carrito/escanear")
def escanear_producto(req: EscanearRequest):
    """
    Se llama cuando la cámara de la tablet lee un QR/código de barras
    al meter el producto en el carrito.
    """
    carrito = CARRITOS.get(req.carrito_id)
    if not carrito:
        raise HTTPException(status_code=404, detail="Carrito no existe")
    producto = PRODUCTOS.get(req.codigo)
    if not producto:
        raise HTTPException(status_code=404, detail="Código no reconocido")

    carrito["items"].append({"codigo": req.codigo, **producto})
    carrito["peso_esperado"] = round(carrito["peso_esperado"] + producto["peso_kg"], 3)
    carrito["total"] += producto["precio"]

    peso_real = leer_celdas_de_carga(carrito["peso_esperado"])

    return {
        "producto": producto,
        "total": carrito["total"],
        "peso_esperado": carrito["peso_esperado"],
        "peso_real_celdas": peso_real,
        "items_en_carro": len(carrito["items"]),
    }


@app.post("/carrito/quitar")
def quitar_producto(req: QuitarRequest):
    """Si el cliente retira un producto del carrito, se resta del total y del peso."""
    carrito = CARRITOS.get(req.carrito_id)
    if not carrito:
        raise HTTPException(status_code=404, detail="Carrito no existe")

    for i, item in enumerate(carrito["items"]):
        if item["codigo"] == req.codigo:
            carrito["items"].pop(i)
            carrito["peso_esperado"] = round(carrito["peso_esperado"] - item["peso_kg"], 3)
            carrito["total"] -= item["precio"]
            break
    else:
        raise HTTPException(status_code=404, detail="Ese producto no está en el carrito")

    peso_real = leer_celdas_de_carga(carrito["peso_esperado"])
    return {
        "total": carrito["total"],
        "peso_esperado": carrito["peso_esperado"],
        "peso_real_celdas": peso_real,
        "items_en_carro": len(carrito["items"]),
    }


@app.get("/carrito/{carrito_id}")
def ver_carrito(carrito_id: str):
    carrito = CARRITOS.get(carrito_id)
    if not carrito:
        raise HTTPException(status_code=404, detail="Carrito no existe")
    return carrito


@app.post("/pago")
def pagar(req: PagoRequest):
    """Simula el pago con tarjeta o celular en la tablet, y genera la boleta/QR."""
    carrito = CARRITOS.get(req.carrito_id)
    if not carrito:
        raise HTTPException(status_code=404, detail="Carrito no existe")
    if not carrito["items"]:
        raise HTTPException(status_code=400, detail="El carrito está vacío")

    # Simulación de la pasarela de pago (siempre aprueba en esta demo)
    codigo_boleta = f"CP-{uuid.uuid4().hex[:10].upper()}"
    carrito["pagado"] = True
    carrito["boleta_qr"] = codigo_boleta
    carrito["hora_pago"] = time.time()
    # Guardamos una "foto" del peso pagado, para comparar después en la salida
    carrito["peso_pagado"] = carrito["peso_esperado"]

    return {
        "aprobado": True,
        "metodo": req.metodo,
        "total_pagado": carrito["total"],
        "boleta_qr": codigo_boleta,
    }


@app.post("/salida/validar")
def validar_salida(req: SalidaRequest):
    """
    Simula el doble pesaje del pórtico de salida:
    compara el peso real medido en la plataforma de salida
    contra lo que el cliente efectivamente pagó.
    """
    carrito = CARRITOS.get(req.carrito_id)
    if not carrito:
        raise HTTPException(status_code=404, detail="Carrito no existe")
    if not carrito["pagado"]:
        return {
        "autorizado": False,
        "mensaje": "El carrito no ha sido pagado. Debes pagar antes de pasar por el pórtico de salida.",
        "peso_pagado": None,
        "peso_real_salida": None,
        "diferencia_kg": None,
    }

    # Peso real medido en la PLATAFORMA DE SALIDA (segundo pesaje, sensor distinto)
    peso_real_salida = leer_celdas_de_carga(carrito["peso_esperado"])
    peso_pagado = carrito["peso_pagado"]
    diferencia = round(abs(peso_real_salida - peso_pagado), 3)

    TOLERANCIA_KG = 0.5  # igual que en el diagrama: alerta si delta > 0.5 kg

    if diferencia <= TOLERANCIA_KG:
        return {
            "autorizado": True,
            "peso_pagado": peso_pagado,
            "peso_real_salida": peso_real_salida,
            "diferencia_kg": diferencia,
            "mensaje": "Peso validado. Salida autorizada.",
        }
    else:
        return {
            "autorizado": False,
            "peso_pagado": peso_pagado,
            "peso_real_salida": peso_real_salida,
            "diferencia_kg": diferencia,
            "mensaje": "ALERTA: hay diferencia de peso. Posible producto no pagado.",
        }


@app.get("/")
def home():
    return {"status": "CartPay backend funcionando"}
