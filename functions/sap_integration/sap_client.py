"""
sap_client.py
SAP Web Services SOAP client using zeep.

Provides:
  - SapSoapClient.get_equipos()           → list[dict]  (fleet master data)
  - SapSoapClient.get_costos_equipos()    → list[dict]  (ZWS_GET_KOB1)
  - SapSoapClient.get_inventario()        → list[dict]
  - SapSoapClient.get_partes()            → list[dict]
  - SapSoapClient.get_servicios()         → list[dict]
  - SapSoapClient.get_movimientos()       → list[dict]

Configuration is read from environment variables or passed as constructor args:
  SAP_WSDL_BASE_URL  — base URL for WSDL endpoints
  SAP_USERNAME       — SAP technical user
  SAP_PASSWORD       — SAP technical user password
"""

from __future__ import annotations

import os
import logging
from typing import Any

from zeep import Client, Settings
from zeep.transports import Transport
from requests import Session
from requests.auth import HTTPBasicAuth

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# WSDL endpoint paths (relative to SAP_WSDL_BASE_URL)
# ---------------------------------------------------------------------------
WSDL_EQUIPOS        = "/sap/bc/srt/wsdl/flv_10002A111AD1/bndg_url/sap/bc/srt/rfc/sap/zws_get_equipos/200/zws_get_equipos/ws11?wsdl"
WSDL_KOB1           = "/sap/bc/srt/wsdl/flv_10002A111AD1/bndg_url/sap/bc/srt/rfc/sap/zwm_get_kob1/200/zwm_get_kob1/ws11?wsdl"
WSDL_INVENTARIO     = "/sap/bc/srt/wsdl/flv_10002A111AD1/bndg_url/sap/bc/srt/rfc/sap/zws_get_inventario/200/zws_get_inventario/ws11?wsdl"
WSDL_PARTES         = "/sap/bc/srt/wsdl/flv_10002A111AD1/bndg_url/sap/bc/srt/rfc/sap/zws_get_partes/200/zws_get_partes/ws11?wsdl"
WSDL_SERVICIOS      = "/sap/bc/srt/wsdl/flv_10002A111AD1/bndg_url/sap/bc/srt/rfc/sap/zws_get_servicios/200/zws_get_servicios/ws11?wsdl"
WSDL_MOVIMIENTOS    = "/sap/bc/srt/wsdl/flv_10002A111AD1/bndg_url/sap/bc/srt/rfc/sap/zws_get_movimientos/200/zws_get_movimientos/ws11?wsdl"


class SapSoapClient:
    """Thin wrapper around zeep for SAP Web Services."""

    def __init__(
        self,
        base_url: str | None = None,
        username: str | None = None,
        password: str | None = None,
        timeout: int = 120,
    ):
        self.base_url = base_url or os.environ["SAP_WSDL_BASE_URL"]
        self.username = username or os.environ["SAP_USERNAME"]
        self.password = password or os.environ["SAP_PASSWORD"]
        self.timeout = timeout
        self._clients: dict[str, Client] = {}

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _get_client(self, wsdl_path: str) -> Client:
        if wsdl_path not in self._clients:
            session = Session()
            session.auth = HTTPBasicAuth(self.username, self.password)
            transport = Transport(session=session, timeout=self.timeout)
            settings = Settings(strict=False, xml_huge_tree=True)
            self._clients[wsdl_path] = Client(
                wsdl=f"{self.base_url}{wsdl_path}",
                transport=transport,
                settings=settings,
            )
        return self._clients[wsdl_path]

    @staticmethod
    def _serialize_item(item: Any) -> dict:
        """Recursively convert zeep objects to plain dicts."""
        if hasattr(item, "__dict__"):
            return {k: SapSoapClient._serialize_item(v) for k, v in item.__dict__.items()}
        if isinstance(item, list):
            return [SapSoapClient._serialize_item(i) for i in item]
        return item

    @staticmethod
    def _table_to_list(table_node: Any) -> list[dict]:
        """Convert a SOAP table (list of items) to list[dict]."""
        if table_node is None:
            return []
        items = table_node if isinstance(table_node, list) else getattr(table_node, "item", [])
        return [SapSoapClient._serialize_item(row) for row in items]

    # ------------------------------------------------------------------
    # Public methods
    # ------------------------------------------------------------------
    def get_equipos(self) -> list[dict]:
        """Fetch fleet master data (ZWS_GET_EQUIPOS)."""
        client = self._get_client(WSDL_EQUIPOS)
        response = client.service.ZWS_GET_EQUIPOS()
        logger.info("get_equipos: raw response received")
        return self._table_to_list(response.get("T_EQUIPOS") if isinstance(response, dict) else response)

    def get_costos_equipos(self, fecha_inicio: str, fecha_fin: str) -> list[dict]:
        """Fetch equipment costs (ZWS_GET_KOB1).

        Args:
            fecha_inicio: Start date in format YYYYMMDD.
            fecha_fin:    End date in format YYYYMMDD.
        """
        client = self._get_client(WSDL_KOB1)
        response = client.service.ZWS_GET_KOB1(
            I_FECHA_INICIO=fecha_inicio,
            I_FECHA_FIN=fecha_fin,
        )
        logger.info("get_costos_equipos: raw response received")
        return self._table_to_list(response.get("T_KOB1") if isinstance(response, dict) else response)

    def get_inventario(self) -> list[dict]:
        """Fetch inventory data."""
        client = self._get_client(WSDL_INVENTARIO)
        response = client.service.ZWS_GET_INVENTARIO()
        return self._table_to_list(response.get("T_INVENTARIO") if isinstance(response, dict) else response)

    def get_partes(self) -> list[dict]:
        """Fetch spare parts data."""
        client = self._get_client(WSDL_PARTES)
        response = client.service.ZWS_GET_PARTES()
        return self._table_to_list(response.get("T_PARTES") if isinstance(response, dict) else response)

    def get_servicios(self) -> list[dict]:
        """Fetch services data."""
        client = self._get_client(WSDL_SERVICIOS)
        response = client.service.ZWS_GET_SERVICIOS()
        return self._table_to_list(response.get("T_SERVICIOS") if isinstance(response, dict) else response)

    def get_movimientos(self) -> list[dict]:
        """Fetch accounting movements."""
        client = self._get_client(WSDL_MOVIMIENTOS)
        response = client.service.ZWS_GET_MOVIMIENTOS()
        return self._table_to_list(response.get("T_MOVIMIENTOS") if isinstance(response, dict) else response)
