import modal
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent

IMAGE = (
    modal.Image.debian_slim()
    .pip_install_from_pyproject(
        PROJECT_ROOT / "pyproject.toml",
    )
    .add_local_python_source("apps.zwift_ds_mcp")
)

app = modal.App("zwift-ds-mcp", image=IMAGE)


@app.function(
    secrets=[modal.Secret.from_name("zwift-ds-secret")],
)
@modal.asgi_app()
def mcp_app():
    from apps.mcp_server.app import mcp
    return mcp.http_app(stateless_http=True)
  