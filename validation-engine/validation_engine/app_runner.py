"""
Isolated Application Launcher and Container Status Inspector.
When a database is restored in an isolated environment, starts/attaches a test application
connected specifically to that restored isolated database.
"""
import os
import shutil
import subprocess
from typing import Optional, Dict, Any
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
import httpx


class IsolatedAppLauncher:
    """
    Manages the lifecycle and connectivity of a test application running against
    an isolated restored database.
    """

    def __init__(
        self,
        restored_db_url: str,
        target_app_url: Optional[str] = None,
        container_name: Optional[str] = None
    ):
        self.restored_db_url = restored_db_url
        self.target_app_url = target_app_url.rstrip("/") if target_app_url else None
        self.container_name = container_name
        self.is_started = False
        self._test_client: Optional[Any] = None
        self._engine = None
        self._session_factory = None
        self._startup_error: Optional[str] = None

    def start(self):
        """
        Starts the isolated test application connected to the restored database.
        In local mode, initializes an isolated application runner binding demo_app to the restored DB.
        """
        try:
            if self.target_app_url:
                # Connected to an already running container/instance
                self.is_started = True
                return self

            # Spin up local isolated application instance
            from demo_app.main import app as demo_app
            from demo_app.database import get_db

            connect_args = {"check_same_thread": False} if self.restored_db_url.startswith("sqlite") else {}
            self._engine = create_engine(self.restored_db_url, connect_args=connect_args)
            self._session_factory = sessionmaker(autocommit=False, autoflush=False, bind=self._engine)

            def _override_get_db():
                db = self._session_factory()
                try:
                    yield db
                finally:
                    db.close()

            demo_app.dependency_overrides[get_db] = _override_get_db
            self._test_client = TestClient(demo_app)
            self.is_started = True
            return self

        except Exception as e:
            self.is_started = False
            self._startup_error = str(e)
            raise e

    def stop(self):
        """Stops the isolated test application and clears dependency overrides."""
        try:
            if self._test_client:
                from demo_app.main import app as demo_app
                from demo_app.database import get_db
                demo_app.dependency_overrides.pop(get_db, None)
                if hasattr(self._test_client, "close"):
                    self._test_client.close()
                self._test_client = None
            if self._engine:
                self._engine.dispose()
                self._engine = None
        finally:
            self.is_started = False

    @contextmanager
    def run_context(self):
        """Context manager for automatic starting and clean disposal."""
        self.start()
        try:
            yield self
        finally:
            self.stop()

    def get_client(self):
        """Returns an active HTTP client for the isolated application."""
        if self.target_app_url:
            return httpx.Client(base_url=self.target_app_url, timeout=10.0)
        if self._test_client:
            return self._test_client
        raise RuntimeError("Isolated test application is not started. Call start() first.")

    def inspect_container_status(self) -> Dict[str, Any]:
        """
        Inspects Docker container status if container_name is provided or docker is active.
        Falls back to local application state inspection in standalone environments.
        """
        if self.container_name and shutil.which("docker"):
            try:
                res = subprocess.run(
                    ["docker", "inspect", "--format", "{{.State.Status}}|{{.State.Running}}|{{.State.Health.Status}}", self.container_name],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if res.returncode == 0:
                    parts = res.stdout.strip().split("|")
                    raw_status = parts[0]
                    is_running = parts[1].lower() == "true" if len(parts) > 1 else False
                    health = parts[2] if len(parts) > 2 and parts[2] else "unknown"
                    return {
                        "container_name": self.container_name,
                        "status": raw_status,
                        "running": is_running,
                        "health": health,
                        "error": None
                    }
                else:
                    return {
                        "container_name": self.container_name,
                        "status": "NOT_FOUND",
                        "running": False,
                        "health": "unhealthy",
                        "error": res.stderr.strip()
                    }
            except Exception as e:
                return {
                    "container_name": self.container_name,
                    "status": "DOCKER_INSPECT_ERROR",
                    "running": False,
                    "health": "unknown",
                    "error": str(e)
                }

        # Standalone / Process-level application inspection
        return {
            "container_name": self.container_name or "local-isolated-process",
            "status": "RUNNING" if self.is_started else ("FAILED" if self._startup_error else "STOPPED"),
            "running": self.is_started,
            "health": "healthy" if self.is_started else "unhealthy",
            "error": self._startup_error
        }
