from delta.core.engine import DeltaEngine
from delta.core.config import DeltaConfig
from delta.core.database import Database
from delta.core.session import SessionManager
from delta.ai.intent import IntentEngine
from delta.core.plugin import PluginManager
from delta.core.display import DisplayManager

def test_geotrace_tool_registered_in_engine(tmp_path):
    db_path = str(tmp_path / "delta.db")
    config = DeltaConfig()
    db = Database(db_path)
    db.initialize()
    session = SessionManager(database=db)
    intent = IntentEngine(config=config, database=db)
    plugin_mgr = PluginManager(str(tmp_path / "plugins"))
    display = DisplayManager()

    engine = DeltaEngine(
        config=config,
        database=db,
        session=session,
        intent_engine=intent,
        plugin_manager=plugin_mgr,
        display=display,
        cwd=str(tmp_path)
    )

    tool = engine.tools.get("geotrace_investigate")
    assert tool is not None
    assert tool.category == "osint"
    assert any(p.name == "target" for p in tool.parameters)

    # Test tool invocation via engine
    result = tool.execute(
        target="@johndoe_jakarta",
        operator="tester-01",
        purpose="Legitimate KYC security verification",
        consent_mode=False
    )
    assert result["success"] is True
    assert result["output"] is not None
