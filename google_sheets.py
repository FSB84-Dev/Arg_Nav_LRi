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
    try:
        logger.info("Obteniendo siguiente ID desde columna A...")
        valores = hoja.col_values(1)
        logger.info(f"Valores encontrados en columna A: {len(valores)} total")
        numeros = [int(v) for v in valores[1:] if v.isdigit()]
        siguiente = max(numeros) + 1 if numeros else 1
        logger.info(f"Siguiente ID calculado: {siguiente}")
        return siguiente
    except Exception as e:
        logger.error(f"Error obteniendo siguiente ID: {e}", exc_info=True)
        raise


def buscar_empresa_abierta(hoja, empresa):
    try:
        # get_all_values() es más seguro que get_all_records() para hojas vacías
        all_values = hoja.get_all_values()
        
        # Si solo hay header (1 fila) o está vacía, no hay registros
        if len(all_values) <= 1:
            logger.info("✅ Hoja vacía (solo headers), no hay operaciones abiertas")
            return None, None
        
        # Convertir a records manualmente
        headers = all_values[0]
        registros = []
        for row_idx, row in enumerate(all_values[1:], start=2):  # start=2 porque fila 1 es header
            if len(row) > 0 and any(row):  # Skip filas completamente vacías
                record = {headers[i]: row[i] if i < len(row) else "" for i in range(len(headers))}
                registros.append((row_idx, record))
        
        # Buscar empresa con operación abierta
        for fila_num, reg in registros:
            if (reg.get("Empresa", "").lower() == empresa.lower() and
                    reg.get("Estado_Operacion", "").lower() == "abierta"):
                logger.info(f"⚠️ Operación abierta encontrada en fila {fila_num}")
                return fila_num, reg
        
        logger.info("✅ No hay operaciones abiertas para esta empresa")
        return None, None
        
    except Exception as e:
        logger.error(f"Error buscando empresa abierta: {e}", exc_info=True)
        # En caso de error, devolver None y continuar (mejor crear duplicado que fallar)
        return None, None


def guardar_reunion(datos: dict) -> dict:
    try:
        logger.info("=== INICIANDO GUARDADO EN GOOGLE SHEETS ===")
        logger.info(f"Datos recibidos: {json.dumps(datos, indent=2, ensure_ascii=False)}")
        
        logger.info("Conectando a Google Sheets...")
        hoja = get_hoja()
        logger.info(f"Conectado a hoja: {hoja.title}")
        
        empresa = datos.get("empresa", "")
        logger.info(f"Buscando operaciones abiertas para empresa: '{empresa}'")
        fila_existente, reg_existente = buscar_empresa_abierta(hoja, empresa)
        
        if fila_existente:
            logger.info(f"⚠️ Operación abierta encontrada en fila {fila_existente}: {reg_existente}")
        else:
            logger.info("✅ No hay operaciones abiertas para esta empresa")
        
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
        
        logger.info(f"Fila a insertar ({len(nueva_fila)} columnas): {nueva_fila[:6]}...")
        logger.info("Ejecutando append_row...")
        
        hoja.append_row(nueva_fila)
        
        logger.info(f"✅ Reunion guardada exitosamente en Sheets con ID {siguiente_id}")
        logger.info("=== FIN GUARDADO GOOGLE SHEETS ===")
        
        return {
            "ok": True,
            "id": siguiente_id,
            "operacion_existente": fila_existente is not None,
            "reg_existente": reg_existente
        }
    except Exception as e:
        logger.error(f"❌ ERROR CRÍTICO guardando en Sheets: {e}", exc_info=True)
        logger.error(f"Tipo de error: {type(e).__name__}")
        logger.error(f"Datos que causaron el error: {json.dumps(datos, ensure_ascii=False)}")
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
