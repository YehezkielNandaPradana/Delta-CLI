# tests/test_autonomous_pipeline.py
import pytest
import tempfile
import os
from delta.agent.runtime.pipeline import AutonomousPipeline
from delta.agent.policy.autonomy import AutonomyMode

@pytest.mark.asyncio
async def test_autonomous_pipeline_end_to_end_clean_run():
    with tempfile.TemporaryDirectory() as tmp:
        with open(os.path.join(tmp, "pyproject.toml"), "w") as f:
            f.write("[tool.pytest.ini_options]\n")
        with open(os.path.join(tmp, "calc.py"), "w") as f:
            f.write("def add(a, b):\n    return a + b\n")
        with open(os.path.join(tmp, "test_calc.py"), "w") as f:
            f.write("from calc import add\ndef test_add(): assert add(1, 2) == 3\n")

        pipeline = AutonomousPipeline(workspace_root=tmp, autonomy=AutonomyMode.FULL_AUTONOMOUS)
        res = await pipeline.run(objective="Verify calc.py implementation", target_files=["calc.py"])
        assert res.task_status == "FINISHED"
        assert res.completion_decision.eligible is True
        assert "OBSERVE" in res.lifecycle_history
        assert "FINISH" in res.lifecycle_history
