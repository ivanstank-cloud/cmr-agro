# Guarda este archivo como: main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import List, Optional
import os
import psycopg2

app = FastAPI(title="CRM Agropecuario en la Nube")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATABASE_URL = os.environ.get("DATABASE_URL")

def get_db_connection():
    return psycopg2.connect(DATABASE_URL)

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clientes (
            id SERIAL PRIMARY KEY,
            nombre_establecimiento TEXT NOT NULL,
            contacto_persona TEXT NOT NULL,
            email TEXT,
            telefono TEXT,
            google_maps_url TEXT,
            latitud REAL,
            longitud REAL,
            nivel_contacto TEXT DEFAULT 'Frecuente',
            es_productor INTEGER DEFAULT 0,
            es_planta INTEGER DEFAULT 0,
            es_feedlot INTEGER DEFAULT 0,
            notas TEXT
        )
    """)
    conn.commit()
    cursor.close()
    conn.close()

if DATABASE_URL:
    try:
        init_db()
    except Exception as e:
        print("Error al inicializar la base de datos:", e)

class Cliente(BaseModel):
    id: Optional[int] = None
    nombre_establecimiento: str
    contacto_persona: str
    email: Optional[str] = None
    telefono: Optional[str] = None
    google_maps_url: Optional[str] = None
    latitud: Optional[float] = None
    longitud: Optional[float] = None
    nivel_contacto: str = "Frecuente"
    es_productor: bool = False
    es_planta: bool = False
    es_feedlot: bool = False
    notas: Optional[str] = None

@app.get("/clientes", response_model=List[Cliente])
def obtener_clientes():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, nombre_establecimiento, contacto_persona, email, telefono, 
               google_maps_url, latitud, longitud, nivel_contacto, 
               es_productor, es_planta, es_feedlot, notas 
        FROM clientes
    """)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return [
        Cliente(
            id=r, nombre_establecimiento=r, contacto_persona=r, email=r, telefono=r,
            google_maps_url=r, latitud=r, longitud=r, nivel_contacto=r,
            es_productor=bool(r), es_planta=bool(r), es_feedlot=bool(r), notas=r
        ) for r in rows
    ]

@app.post("/clientes", response_model=Cliente)
def crear_cliente(cliente: Cliente):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO clientes (
            nombre_establecimiento, contacto_persona, email, telefono, google_maps_url, 
            latitud, longitud, nivel_contacto, es_productor, es_planta, es_feedlot, notas
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
    """, (
        cliente.nombre_establecimiento, cliente.contacto_persona, cliente.email, cliente.telefono, 
        cliente.google_maps_url, cliente.latitud, cliente.longitud, cliente.nivel_contacto,
        int(cliente.es_productor), int(cliente.es_planta), int(cliente.es_feedlot), cliente.notas
    ))
    cliente.id = cursor.fetchone()
    conn.commit()
    cursor.close()
    conn.close()
    return cliente

@app.delete("/clientes/{cliente_id}")
def eliminar_cliente(cliente_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM clientes WHERE id = %s", (cliente_id,))
    rows_affected = cursor.rowcount
    conn.commit()
    cursor.close()
    conn.close()
    if rows_affected == 0:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return {"message": "Cliente eliminado correctamente"}

