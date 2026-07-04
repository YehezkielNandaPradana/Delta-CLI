# delta/plugins/__init__.py
"""
Delta Plugin Package.
Place custom plugin .py files in this directory and they will be auto-discovered.
Example plugin structure:

class MyPlugin(PluginBase):
    name = "my-plugin"
    version = "1.0.0"
    description = "My custom plugin"
    commands = ["mycommand"]
    
    def execute(self, command, args, context):
        return "Plugin executed!"
"""