"""Google Cloud Secret Manager integration for loading API keys."""

import os
from typing import Optional
from google.cloud import secretmanager
from google.api_core import exceptions
from .debug_config import debug_print


class SecretManagerClient:
    """Client for accessing Google Cloud Secret Manager."""
    
    def __init__(self, project_id: str = None):
        """Initialize the Secret Manager client.
        
        Args:
            project_id: GCP project ID (defaults to GOOGLE_CLOUD_PROJECT env var)
        """
        self.project_id = project_id or os.getenv("GOOGLE_CLOUD_PROJECT", "proj-roth")
        self._client = None
    
    def _get_client(self):
        """Lazy initialization of Secret Manager client."""
        if self._client is None:
            try:
                self._client = secretmanager.SecretManagerServiceClient()
            except Exception as e:
                debug_print(f"[DEBUG] Failed to initialize Secret Manager client: {e}")
                return None
        return self._client
    
    def get_secret(self, secret_name: str, version: str = "latest") -> Optional[str]:
        """Retrieve a secret from Google Cloud Secret Manager.
        
        Args:
            secret_name: Name of the secret (e.g., 'google-maps-api-key')
            version: Version of the secret (default: 'latest')
            
        Returns:
            The secret value as a string, or None if not found
        """
        client = self._get_client()
        if not client:
            return None
            
        try:
            # Build the resource name
            name = f"projects/{self.project_id}/secrets/{secret_name}/versions/{version}"
            
            # Access the secret
            response = client.access_secret_version(request={"name": name})
            secret_value = response.payload.data.decode("UTF-8")
            
            debug_print(f"[DEBUG] Successfully loaded secret '{secret_name}' from Secret Manager")
            return secret_value.strip()
            
        except exceptions.NotFound:
            debug_print(f"[DEBUG] Secret '{secret_name}' not found in Secret Manager")
            return None
        except exceptions.PermissionDenied:
            debug_print(f"[DEBUG] Permission denied accessing secret '{secret_name}'")
            return None
        except Exception as e:
            debug_print(f"[DEBUG] Error accessing secret '{secret_name}': {e}")
            return None


# Singleton instance
_secret_manager = None


def get_secret_manager() -> SecretManagerClient:
    """Get or create the singleton SecretManagerClient instance."""
    global _secret_manager
    if _secret_manager is None:
        _secret_manager = SecretManagerClient()
    return _secret_manager


def load_secret(secret_name: str, fallback_env_var: Optional[str] = None) -> Optional[str]:
    """Load a secret from Secret Manager with optional environment variable fallback.
    
    Args:
        secret_name: Name of the secret in Secret Manager
        fallback_env_var: Optional environment variable to check if Secret Manager fails
        
    Returns:
        The secret value or None if not found
    """
    # Try Secret Manager first
    manager = get_secret_manager()
    value = manager.get_secret(secret_name)
    
    if value:
        return value
    
    # Fall back to environment variable if provided
    if fallback_env_var:
        value = os.getenv(fallback_env_var)
        if value:
            debug_print(f"[DEBUG] Using {fallback_env_var} environment variable for {secret_name}")
            return value
    
    return None