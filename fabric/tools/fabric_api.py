"""Operaciones del perfil Fabric que la CLI ``fab`` no cubre (WRK-TASK-099).

Uso (desde la raíz del repo, con el extra ``[fabric]`` o ``uv run --with azure-identity``):

    python fabric/tools/fabric_api.py --env-file <ruta a fabric.env> check-access --as sp
    python fabric/tools/fabric_api.py --env-file <ruta a fabric.env> publish-wheel dist/<wheel>

``fabric.env`` vive fuera del repositorio y define FABRIC_TENANT_ID, FABRIC_CLIENT_ID,
FABRIC_CLIENT_CERT_PATH y FABRIC_WORKSPACE_NAME. Ningún identificador ni token se imprime: la
salida sólo usa nombres de items y estados.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path
from typing import Any

import httpx

API = "https://api.fabric.microsoft.com/v1"
SCOPE = "https://api.fabric.microsoft.com/.default"
ENVIRONMENT_NAME = "ragdocs_env"
SQL_DATABASE_NAME = "ragdocs_vectors"
REQUIRED_ITEMS = {
    ("ragdocs_eval", "Lakehouse"),
    ("ragdocs_vectors", "SQLDatabase"),
    ("ragdocs_env", "Environment"),
    ("ragdocs_params", "VariableLibrary"),
}


def load_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip()
    return values


def write_env_values(path: Path, values: dict[str, str]) -> None:
    """Replace or append ``KEY=value`` lines without printing the values."""
    lines = [
        line
        for line in path.read_text(encoding="utf-8-sig").splitlines()
        if line.split("=", 1)[0].strip() not in values
    ]
    lines.extend(f"{key}={value}" for key, value in values.items())
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def credential(config: dict[str, str], identity: str) -> Any:
    from azure.identity import AzureCliCredential, CertificateCredential

    if identity == "user":
        return AzureCliCredential()
    return CertificateCredential(
        tenant_id=config["FABRIC_TENANT_ID"],
        client_id=config["FABRIC_CLIENT_ID"],
        certificate_path=config["FABRIC_CLIENT_CERT_PATH"],
    )


class FabricClient:
    def __init__(self, config: dict[str, str], identity: str) -> None:
        token = credential(config, identity).get_token(SCOPE).token
        self.http = httpx.Client(
            base_url=API, headers={"Authorization": f"Bearer {token}"}, timeout=120
        )
        self.workspace_name = config["FABRIC_WORKSPACE_NAME"]

    def _get(self, path: str) -> dict[str, Any]:
        response = self.http.get(path)
        response.raise_for_status()
        return response.json()

    def workspace_id(self) -> str:
        for workspace in self._get("/workspaces").get("value", []):
            if workspace["displayName"] == self.workspace_name:
                return workspace["id"]
        raise SystemExit(f"Workspace '{self.workspace_name}' no visible para esta identidad.")

    def items(self, workspace_id: str) -> dict[tuple[str, str], str]:
        return {
            (item["displayName"], item["type"]): item["id"]
            for item in self._get(f"/workspaces/{workspace_id}/items").get("value", [])
        }

    def sql_connection(self) -> tuple[str, str]:
        workspace_id = self.workspace_id()
        database_id = self.items(workspace_id)[(SQL_DATABASE_NAME, "SQLDatabase")]
        properties = self._get(f"/workspaces/{workspace_id}/sqlDatabases/{database_id}")[
            "properties"
        ]
        return str(properties["serverFqdn"]), str(properties["databaseName"])

    def publish_wheel(self, wheel: Path, timeout_s: int) -> str:
        workspace_id = self.workspace_id()
        environment_id = self.items(workspace_id)[(ENVIRONMENT_NAME, "Environment")]
        base = f"/workspaces/{workspace_id}/environments/{environment_id}"
        with wheel.open("rb") as handle:
            response = self.http.post(
                f"{base}/staging/libraries",
                files={"file": (wheel.name, handle, "application/octet-stream")},
            )
        if response.status_code >= 400:
            raise SystemExit(
                f"Subida del wheel rechazada: HTTP {response.status_code} {response.text}"
            )
        response = self.http.post(f"{base}/staging/publish")
        if response.status_code >= 400:
            raise SystemExit(f"Publicación rechazada: HTTP {response.status_code} {response.text}")
        deadline = time.monotonic() + timeout_s
        state = "unknown"
        while time.monotonic() < deadline:
            details = self._get(base).get("properties", {}).get("publishDetails", {})
            state = str(details.get("state", "unknown")).lower()
            if state in {"success", "failed", "cancelled"}:
                break
            time.sleep(30)
        return state


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--env-file", type=Path, required=True)
    commands = parser.add_subparsers(dest="command", required=True)
    check = commands.add_parser("check-access")
    check.add_argument("--as", dest="identity", choices=["user", "sp"], default="sp")
    sql = commands.add_parser(
        "sql-connection",
        help="Escribe FABRIC_SQL_SERVER y FABRIC_SQL_DATABASE en el fichero de entorno.",
    )
    sql.add_argument("--as", dest="identity", choices=["user", "sp"], default="sp")
    publish = commands.add_parser("publish-wheel")
    publish.add_argument("wheel", type=Path)
    publish.add_argument("--as", dest="identity", choices=["user", "sp"], default="user")
    publish.add_argument("--timeout", type=int, default=1800)
    args = parser.parse_args()

    client = FabricClient(load_env_file(args.env_file), args.identity)
    if args.command == "check-access":
        found = set(client.items(client.workspace_id()))
        missing = REQUIRED_ITEMS - found
        for name, kind in sorted(REQUIRED_ITEMS):
            print(f"{'ok' if (name, kind) not in missing else 'FALTA'}: {name}.{kind}")
        return 1 if missing else 0
    if args.command == "sql-connection":
        server, database = client.sql_connection()
        write_env_values(
            args.env_file, {"FABRIC_SQL_SERVER": server, "FABRIC_SQL_DATABASE": database}
        )
        print(f"Conexión SQL de {SQL_DATABASE_NAME} guardada en el fichero de entorno.")
        return 0
    state = client.publish_wheel(args.wheel, args.timeout)
    print(f"Publicación del Environment {ENVIRONMENT_NAME}: {state}")
    return 0 if state == "success" else 1


if __name__ == "__main__":
    sys.exit(main())
