# delta/modules/__init__.py
"""Delta Security Assessment Modules."""
from delta.modules.scanner import ScannerModule
from delta.modules.network import NetworkModule
from delta.modules.web import WebModule
from delta.modules.dns import DNSModule
from delta.modules.ssl import SSLModule
from delta.modules.crypto import CryptoModule
from delta.modules.encode import EncodeModule
from delta.modules.report import ReportModule
from delta.modules.analysis import AnalysisModule