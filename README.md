# Delta - AI-Powered Cyber Security Assessment CLI



[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

[![GitHub Stars](https://img.shields.io/github/stars/hackerai/delta?style=social)](https://github.com/hackerai/delta)

[![GitHub Forks](https://img.shields.io/github/forks/hackerai/delta?style=social)](https://github.com/hackerai/delta)



Delta is a modern AI-powered Command Line Interface designed for cybersecurity professionals, penetration testers, and system administrators. It combines artificial intelligence with professional security testing tools to provide an intuitive, natural language interface for conducting security assessments, vulnerability scanning, and penetration testing on authorized systems.



## 🚀 Features



### Core Capabilities

- **🤖 AI Natural Language Interface** - Understands and executes commands like "scan localhost", "check security on 192.168.1.1", or "audit wordpress site"

- **🔍 Network Scanning** - Comprehensive port scanning, service detection, banner grabbing, and OS fingerprinting

- **🌐 Web Application Analysis** - HTTP header analysis, security misconfiguration detection, technology stack identification

- **🔒 SSL/TLS Security Assessment** - Certificate validation, protocol analysis, cipher suite evaluation, and vulnerability checking

- **📡 DNS Enumeration & Intelligence** - DNS record enumeration, reverse DNS lookup, zone transfer testing, and WHOIS information gathering

- **🛡 Password Security Analysis** - Strength assessment, entropy calculation, and policy compliance checking

- **🔐 Cryptographic Tools** - Hash identification, generation, encoding/decoding utilities for security testing

- **📊 Professional Reporting** - Automated report generation in Markdown, HTML, and JSON formats

- **🧩 Extensible Plugin System** - Modular architecture for adding custom security tools and scanners

- **💾 Persistent Session Memory** - Context-aware command history and session management across executions

- **📚 Built-in Knowledge Base** - Vulnerability database with explanations, remediation guidance, and reference materials

- **🌙 Offline-First Design** - All operations run locally without requiring internet connectivity

- **⚡ High Performance** - Optimized for speed with minimal dependencies



### Security Modules

- **Network Scanner** - TCP/UDP port scanning, service version detection

- **Web Analyzer** - HTTP security headers, technology detection, directory enumeration

- **SSL/TLS Checker** - Certificate validation, protocol weaknesses, cipher analysis

- **DNS Enumerator** - Record types, zone transfers, subdomain discovery

- **Crypto Tools** - Hash algorithms, encoding/decoding, cryptographic utilities

- **Password Analyzer** - Strength assessment, entropy calculation, policy validation

- **Report Generator** - Professional security reports in multiple formats



## 📋 Installation



### Quick Install (PyPI)

```bash

# Basic installation

pip install delta-security



# Enhanced UI installation (recommended)

pip install delta-security[all]

```



### Development Installation

```bash

# Clone the repository

git clone https://github.com/hackerai/delta.git

cd delta



# Install in development mode

pip install -e .



# Install with optional dependencies

pip install -e .[all]

```



### From Source

```bash

# Download latest release

wget https://github.com/hackerai/delta/archive/refs/tags/v1.0.0.tar.gz

tar -xzf v1.0.0.tar.gz

cd delta-1.0.0



# Install

pip install .

```



## 🚀 Usage



### Starting Delta

```bash

# Using the command line interface

delta



# Or using Python module syntax

python3 -m delta

```



### Basic Commands

Once Delta is running, you can use natural language commands:



```

Δ > scan localhost

Δ > check security on 192.168.1.100

Δ > audit wordpress site example.com

Δ > enumerate network 192.168.1.0/24

Δ > analyze scan results

Δ > explain SQL injection

Δ > generate security report

Δ > help

```



### Command Reference



| Command | Description | Example |

|---------|-------------|---------|

| `scan <target>` | Scan target for open ports and services | `scan 192.168.1.1` |

| `audit <target>` | Perform comprehensive security audit | `audit example.com` |

| `enumerate <target>` | Enumerate network/DNS information | `enumerate 192.168.1.0/24` |

| `check <target>` | Check specific security aspects | `check ssl example.com:443` |

| `dns <domain>` | Perform DNS lookup | `dns google.com` |

| `whois <domain>` | WHOIS information lookup | `whois example.com` |

| `ssl <host:port>` | SSL/TLS certificate analysis | `ssl example.com:443` |

| `ping <host>` | Network connectivity test | `ping 8.8.8.8` |

| `password <pwd>` | Analyze password strength | `password MySecurePass123!` |

| `hash <data>` | Hash operations and identification | `hash testdata` |

| `decode <type> <data>` | Decode base64/hex/url/jwt | `decode base64 dGhpcyBpcyBhIHRlc3Q=` |

| `analyze <target>` | Analyze previous scan results | `analyze last` |

| `explain <vuln>` | Get vulnerability explanation | `explain XSS` |

| `report` | Generate security report | `report` |

| `history` | Show command history | `history` |

| `help` | Display help information | `help` |



### Advanced Usage Examples



#### Network Reconnaissance

```bash

Δ > scan 192.168.1.0/24 --top-ports 1000

Δ > enumerate 10.0.0.0/16 --dns-zone-transfer

Δ > whois example.com

```



#### Web Application Testing

```bash

Δ > audit https://example.com --spider --forms

Δ > check headers https://example.com

Δ > scan example.com --ports 80,443,8080,8443

```



#### SSL/TLS Assessment

```bash

Δ > ssl example.com:443 --check-protocols --check-ciphers

Δ > ssl mail.example.com:993 --verbose

```



#### Password Security

```bash

Δ > password MyP@ssw0rd123!

Δ > password --generate --length 16 --special-chars

```



#### Cryptographic Operations

```bash

Δ > hash "secret message" --algorithm sha256

Δ > decode base64 SGVsbG8gV29ybGQ=

Δ > encode hex "Hello World"

```



#### Reporting

```bash

Δ > report --format markdown --output security-assessment.md

Δ > report --format html --output report.html --template executive

Δ > report --format json --output findings.json

```



## 🔧 Configuration



Delta can be customized through configuration files and environment variables.



### Configuration File

Create `~/.delta/config.yaml` or `/etc/delta/config.yaml`:



```yaml

# Delta Configuration File

general:

  theme: "dark"

  output_format: "markdown"

  report_dir: "~/delta-reports"

  max_threads: 50

  timeout: 30



scanner:

  timing: "T4"

  service_detection: true

  os_detection: true

  version_intensity: 9



web:

  user_agent: "Delta-Security-Scanner/1.0"

  follow_redirects: true

  timeout: 10



ssl:

  check_protocols: true

  check_ciphers: true

  certificate_transparency: true



logging:

  level: "INFO"

  file: "~/delta.log"

  max_size: "10MB"

  backup_count: 5

```



### Environment Variables

```bash

DELTA_CONFIG_DIR=/path/to/config

DELTA_DATA_DIR=/path/to/data

DELTA_LOG_LEVEL=DEBUG

DELTA_MAX_THREADS=100

```



## 📁 Project Structure



```

delta/

├── __init__.py

├── __main__.py          # Entry point for `python -m delta`

├── main.py              # Main application entry point

├── ai/                  # Artificial intelligence components

│   ├── __init__.py

│   ├── intent.py        # Natural language understanding

│   └── knowledge.py     # Security knowledge base

├── config/              # Configuration management

│   ├── __init__.py

│   └── settings.py

├── core/                # Core engine and utilities

│   ├── __init__.py

│   ├── engine.py        # Main Delta engine

│   ├── config.py        # Configuration handling

│   ├── database.py      # SQLite database for history/cache

│   ├── session.py       # Session management

│   └── display.py       # Terminal UI/display

├── knowledge/           # Security vulnerability database

│   ├── __init__.py

│   └── vulnerabilities.json

├── modules/             # Security testing modules

│   ├── __init__.py

│   ├── analysis.py      # Result analysis and correlation

│   ├── crypto.py        # Cryptographic utilities

│   ├── dns.py           # DNS enumeration tools

│   ├── encode.py        # Encoding/decoding utilities

│   ├── network.py       # Network scanning utilities

│   ├── report.py        # Report generation

│   ├── scanner.py       # Port scanning implementation

│   ├── ssl.py           # SSL/TLS analysis

│   └── web.py           # Web application analysis

├── plugins/             # Plugin system

│   ├── __init__.py

│   └── base.py          # Base plugin class

├── templates/           # Report templates

│   ├── __init__.py

│   ├── markdown.md

│   ├── html.html

│   └── json.json

└── utils/               # Utility functions

    ├── __init__.py

    ├── helpers.py

    └── validators.py

```



## 🐳 Docker Usage



### Official Docker Image

```bash

# Pull the official image

docker pull hackerai/delta:latest



# Run with volume mounting for reports

docker run -it --rm \

  -v $(pwd)/reports:/delta/reports \

  hackerai/delta:latest \

  delta scan example.com

```



### Building Custom Image

```bash

# Build from Dockerfile

docker build -t delta-security .



# Run custom build

docker run -it --rm \

  -v $(pwd)/config:/root/.delta \

  -v $(pwd)/reports:/delta/reports \

  delta-security \

  delta audit internal-network.local

```



Dockerfile:

```dockerfile

FROM python:3.11-slim



WORKDIR /app



# Install system dependencies

RUN apt-get update && apt-get install -y \

    nmap \

    && rm -rf /var/lib/apt/lists/*



# Copy and install Delta

COPY . .

RUN pip install -e .[all]



# Create non-root user

RUN useradd -m deltauser

USER deltauser



# Default command

ENTRYPOINT ["delta"]

```



## 🧪 Testing



### Running Tests

```bash

# Run all tests

python -m pytest tests/



# Run specific test suite

python -m pytest tests/test_network.py -v



# Run with coverage

python -m pytest tests/ --cov=delta --cov-report=html

```



### Test Categories

- **Unit Tests** - Individual component testing

- **Integration Tests** - Module interaction testing

- **Functional Tests** - End-to-end command testing

- **Security Tests** - Safe testing of security functionalities



## 📖 Documentation



### Official Documentation

- [User Guide](https://docs.hackerai.co/delta/user-guide)

- [API Reference](https://docs.hackerai.co/delta/api-reference)

- [Module Documentation](https://docs.hackerai.co/delta/modules)

- [Plugin Development Guide](https://docs.hackerai.co/delta/plugins)

- [Configuration Guide](https://docs.hackerai.co/delta/configuration)



### Quick References

- [Command Cheat Sheet](https://docs.hackerai.co/delta/cheat-sheet)

- [Module Reference](https://docs.hackerai.co/delta/module-reference)

- [Configuration Options](https://docs.hackerai.co/delta/config-options)



## 🤝 Contributing



We welcome contributions from the security community! Please read our [Contributing Guidelines](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.



### Development Setup

```bash

# Fork and clone the repository

git clone https://github.com/your-username/delta.git

cd delta



# Create a virtual environment

python -m venv venv

source venv/bin/activate  # On Windows: venv\Scripts\activate



# Install development dependencies

pip install -e .[dev,all]

pip install -r requirements-dev.txt



# Run tests

python -m pytest tests/



# Format code

black delta/ tests/

isort delta/ tests/

```



### Contribution Guidelines

1. Fork the repository

2. Create your feature branch (`git checkout -b feature/amazing-feature`)

3. Make your changes

4. Add tests for new functionality

5. Ensure all tests pass

6. Commit your changes (`git commit -m 'Add amazing feature'`)

7. Push to the branch (`git push origin feature/amazing-feature`)

8. Open a Pull Request



Please follow our [Code of Conduct](CODE_OF_CONDUCT.md) in all interactions.



## 🔐 Legal and Ethical Use



**IMPORTANT:** Delta is designed for authorized security testing only. Users must:



- Obtain explicit written permission before testing any systems

- Comply with all applicable laws and regulations

- Use Delta only on systems they own or have authorization to test

- Respect privacy and data protection regulations

- Understand that unauthorized scanning is illegal in most jurisdictions



The developers assume no liability for misuse of this tool. By using Delta, you agree to use it responsibly and ethically.



## 📄 License



Delta is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.



```

MIT License



Copyright (c) 2026 HackerAI



Permission is hereby granted, free of charge, to any person obtaining a copy

of this software and associated documentation files (the "Software"), to deal

in the Software without restriction, including without limitation the rights

to use, copy, modify, merge, publish, distribute, sublicense, and/or sell

copies of the Software, and to permit persons to whom the Software is

furnished to do so, subject to the following conditions:



The above copyright notice and this permission notice shall be included in all

copies or substantial portions of the Software.



THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR

IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,

FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE

AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER

LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,

OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE

SOFTWARE.

```



## 🙋 Support



- **Documentation**: https://docs.hackerai.co/delta

- **Issue Tracker**: https://github.com/hackerai/delta/issues

- **Discussions**: https://github.com/hackerai/delta/discussions

- **Security Reports**: security@hackerai.co (for responsible disclosure)

- **Email Support**: support@hackerai.co

- **Community Forum**: https://forum.hackerai.co/c/delta



## 📊 Project Statistics



![Lines of Code](https://img.shields.io/tokei/lines/github/hackerai/delta)

![GitHub last commit](https://img.shields.io/github/last-commit/hackerai/delta)

![GitHub issues](https://img.shields.io/github/issues/hackerai/delta)

![GitHub pull requests](https://img.shields.io/github/issues-pr/hackerai/delta)

![GitHub contributors](https://img.shields.io/github/contributors/hackerai/delta)



## 🏆 Acknowledgments



Delta builds upon and integrates with various open-source security tools and libraries. Special thanks to:



- The Nmap Project for network scanning inspiration

- OpenSSL and LibreSSL teams for cryptographic foundations

- OWASP for web security testing methodologies

- The Python security community for valuable libraries and frameworks

- All contributors who have helped improve Delta through feedback and contributions



---



**Delta - Empowering security professionals with AI-powered assessment tools**



*Stay secure. Stay informed. Stay delta.*