import modal
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent

IMAGE = (
    modal.Image.debian_slim()
    .pip_install_from_pyproject(
        PROJECT_ROOT / "pyproject.toml",
    )
    .add_local_python_source("apps.zwift_ds_api")
)

app = modal.App("zwift-ds-api", image=IMAGE)


@app.function(
    secrets=[modal.Secret.from_name("zwift-ds-secret")],
)
@modal.asgi_app()
def fastapi_app():
    from apps.zwift_ds_api.app import app as web_app

    return web_app
