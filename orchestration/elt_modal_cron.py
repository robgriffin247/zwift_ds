import modal
from pathlib import Path 
import subprocess

PROJECT_ROOT = Path(__file__).parent.parent
DBT_ROOT = "/root"

IMAGE = (
    modal.Image.debian_slim()
    .pip_install_from_pyproject(
        PROJECT_ROOT / "pyproject.toml",
    )
    .add_local_dir(PROJECT_ROOT / "orchestration", "/root/orchestration")
    .add_local_dir(PROJECT_ROOT / "ingestion", "/root/ingestion")
    .add_local_dir(PROJECT_ROOT / "models", f"{DBT_ROOT}/models")
    .add_local_dir(PROJECT_ROOT / "macros", f"{DBT_ROOT}/macros")
    .add_local_file(PROJECT_ROOT / "dbt_project.yml", f"{DBT_ROOT}/dbt_project.yml")
    .add_local_file(PROJECT_ROOT / "profiles.yml", f"{DBT_ROOT}/profiles.yml")
    # .add_local_file(PROJECT_ROOT / "packages.yml", f"{DBT_ROOT}/packages.yml")
    # .add_local_file(PROJECT_ROOT / "package-lock.yml", f"{DBT_ROOT}/package-lock.yml")
)

app = modal.App("zwift-ds-elt", image=IMAGE)

@app.function(
    schedule=modal.Cron("20 14 * 3 *"),
    secrets=[modal.Secret.from_name("zwift-ds-secret")],
    timeout=120,
    retries=2,
)
def run_dbt() -> None:
    dbt_flags = ["--project-dir", DBT_ROOT, "--profiles-dir", DBT_ROOT]
    subprocess.run(["dbt", "deps", *dbt_flags], check=True)
    subprocess.run(["dbt", "build", *dbt_flags], check=True)
    return