import uuid
import os


def get_temp_path() -> str:
    base_tmp_path = "/tmp/graxon"

    # Create unique folder using UUID
    run_id = str(uuid.uuid4())
    run_path = os.path.join(base_tmp_path, run_id)

    # Ensure directory exists
    os.makedirs(run_path, exist_ok=True)
    return run_path
