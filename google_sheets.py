import gspread
import json
import logging
import os
from datetime import datetime
from google.oauth2.service_account import Credentials

logger = logging.getLogger(__name__)

SPREADSHEET_ID = "1qWMsW8jyWwkXtpDg1OX8DLjkpniKqLDX_bZTR-hAvOQ"
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

COLUMNAS = [
    "ID", "FechaReunion", "Empresa", "Contacto", "Tipo", "Linea",
    "Resumen", "Proximos_Pasos", "Estado_Lead", "Objeciones", "Productos",
    "Presupuesto", "Importe", "Descuento", "Precio_Verificado", "Importe_Final",
    "Condiciones_Pago", "Pagos_Siguientes", "Alerta_Pago", "Alerta_Material",
    "Estado_Operacion"
]


def get_cliente_sheets():
    creds_json = os.getenv("GOOGLE_CREDENTIALS", "")
    if not creds_json:
        raise ValueError("GOOGLE_CREDENTIALS no configurado")
    creds_dict = json.loads(creds_json)
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    return gspread.authorize(creds)


def get_hoja():
    client = get_cliente_sheets()
    return client.open_by_key(SPREADSHEET_ID).sheet1


def get_siguiente_id(hoja):
    valores = hoja.col_values(1)
    numeros = [int(v) for v in valores[1:] if v.isdigit()]
    return max(numeros) + 1 if numeros else 1


def buscar_empresa_abierta(hoja, empresa):
    registros = hoja.get_all_records()
    for i, reg in enumerate(registros):
        if (reg.get("Empresa", "").lower() == empresa.lower() and
                reg.get("Estado_Operacion", "").lower() == "abierta"):
            return i + 2, reg  # +2 por header y 0-index
    return None, None


def guardar_reunion(datos: dict) -> dict:
    try:
        hoja = get_hoja()
        empresa = datos.get("empresa", "")
        fila_existente, reg_existente = buscar_empresa_abierta(hoja, empresa)
        siguiente_id = get_siguiente_id(hoja)
        fecha_hoy = datetime.now().strftime("%d/%m/%Y")
        nueva_fila = [
            siguiente_id,
            datos.get("fecha_reunion") or fecha_hoy,
            datos.get("empresa", ""),
            datos.get("contacto", ""),
            datos.get("tipo", "Objetivo"),
            datos.get("linea", ""),
            datos.get("resumen", ""),
            datos.get("proximos_pasos", ""),
            datos.get("estado_lead", "Nuevo"),
            datos.get("objeciones", ""),
            datos.get("productos", ""),
            "", "", "", "No", "", "", "", "", "", "Abierta"
        ]
        hoja.append_row(nueva_fila)
        logger.info(f"Reunion guardada en Sheets con ID {siguiente_id}")
        return {
            "ok": True,
            "id": siguiente_id,
            "operacion_existente": fila_existente is not None,
            "reg_existente": reg_existente
        }
    except Exception as e:
        logger.error(f"Error guardando en Sheets: {e}")
        return {"ok": False, "error": str(e)}


def actualizar_fila(fila: int, datos: dict):
    try:
        hoja = get_hoja()
        for col_idx, col_name in enumerate(COLUMNAS, start=1):
            campo = col_name.lower()
            if campo in datos:
                hoja.update_cell(fila, col_idx, datos[campo])
        return {"ok": True}
    except Exception as e:
        logger.error(f"Error actualizando fila: {e}")
        return {"ok": False, "error": str(e)}


def cerrar_operacion(fila: int):
    try:
        hoja = get_hoja()
        col_estado = COLUMNAS.index("Estado_Operacion") + 1
        hoja.update_cell(fila, col_estado, "Cerrada")
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}
