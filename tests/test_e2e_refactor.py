import asyncio
import tempfile
from delta.core.engine import DeltaEngine
from delta.core.config import DeltaConfig
from delta.core.database import Database
from delta.core.session import SessionManager
from delta.ai.intent import IntentEngine
from delta.core.plugin import PluginManager
from delta.core.display import DisplayManager

def test_full_engine_lifecycle():
    async def _test():
        config = DeltaConfig()
        db = Database(":memory:")
        db.initialize()
        session = SessionManager(database=db)
        intent = IntentEngine(config=config, database=db)
        plugin = PluginManager(plugin_dir=tempfile.gettempdir())
        display = DisplayManager()

        engine = DeltaEngine(
            config=config,
            database=db,
            session=session,
            intent_engine=intent,
            plugin_manager=plugin,
            display=display
        )

        await engine.initialize()
        status = await engine.get_status()
        assert status["initialized"] is True
        await engine.shutdown()
        status_after = await engine.get_status()
        assert status_after["initialized"] is False

    asyncio.run(_test())
