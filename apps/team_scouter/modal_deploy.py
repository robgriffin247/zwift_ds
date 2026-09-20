import modal
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
APP_REMOTE_PATH = "/root/app.py"

IMAGE = (
    modal.Image.debian_slim()
    .pip_install_from_pyproject(
        PROJECT_ROOT / "pyproject.toml",
    )
    .add_local_file(PROJECT_ROOT / "apps" / "team_scouter" / "app.py", APP_REMOTE_PATH)
)

app = modal.App("zwift-ds-team-scouter", image=IMAGE)


@app.function(
    secrets=[modal.Secret.from_name("zwift-ds-secret")],
)
@modal.concurrent(max_inputs=100)
@modal.web_server(8000)
def streamlit_app():
    cmd = (
        f"streamlit run {APP_REMOTE_PATH} "
        "--server.port 8000 --server.enableCORS=false --server.enableXsrfProtection=false"
    )
    subprocess.Popen(cmd, shell=True)
