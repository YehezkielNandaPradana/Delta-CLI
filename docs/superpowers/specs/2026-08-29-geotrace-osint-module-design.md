# GeoTrace OSINT Geolocation Module - Design Document

- **Date**: 2026-08-29
- **Status**: Approved
- **Target Subsystem**: `delta/modules/geotrace/`, `delta/ai/tools.py`, `delta/web/`

---

## 1. Overview & Objectives
GeoTrace is a modular OSINT geolocation intelligence engine built for Delta AI Agent. It estimates geographic locations and clusters of public social media accounts strictly using publicly available endpoints and metadata without scraping private areas or violating Terms of Service.

### Key Capabilities
- **Multi-Vector Evidence Extraction**: EXIF metadata, explicit user geotags, visual scene analysis (landmarks, license plates, signage), textual profile context, and posting timestamp timezone distribution.
- **Evidence-Weighted Credibility Scorer**: Confidence scoring (0-100%) with cross-validation clustering and multi-source corroboration boost.
- **Privacy & Anti-Doxxing Safeguards**: Automatic coordinate resolution quantization (~5 km radius) in non-consent mode; refusal of private accounts and heuristic detection of underage accounts.
- **Immutable Cryptographic Audit Trail**: SQLite append-only log with SHA-256 hash-chaining verification for all queries.
- **Web UI & Delta Tool Integration**: Interactive sidebar view in Delta Workstation and schema-registered tool calling.

---

## 2. Architecture & Directory Structure

```text
delta/modules/geotrace/
├── __init__.py           # Package exports (GeoTraceEngine, models, helpers)
├── audit.py              # Hash-chained SQLite audit logger & SafetyGate evaluation
├── collector.py          # Input normalizer & public profile/media data representations
├── extractor.py          # Candidate location extractors across 5 signal vectors
├── scorer.py             # Credibility scorer, cluster analyzer & confidence calculators
├── report.py             # JSON and Human-readable Markdown report generators
├── vision_adapter.py     # Hybrid vision adapter (LLM Vision with heuristic fallback)
└── README.md             # Legal & Compliance documentation (UU PDP No. 27/2022, GDPR)
```

---

## 3. Data Pipeline & Components

### 3.1 `collector.py` (Data Ingestion & Normalization)
- Normalizes inputs (URLs/handles for X/Twitter, Instagram, Threads, Bluesky, Generic).
- Parses EXIF GPS tags into standard decimal degrees.
- Data structures: `MediaMetadata`, `PublicPostData`, `PublicProfileData`.

### 3.2 `extractor.py` (Multi-Source Extraction)
Extracts `LocationCandidate` records across 5 primary sources:
1. `EXIF_GPS`: Embedded image EXIF coordinates and camera models.
2. `EXPLICIT_GEOTAG`: User-tagged check-ins/locations on posts.
3. `VISUAL_AI`: Visual indicators (landmarks, Indonesian vehicle plate prefixes like `B`, `D`, `AB`, signage).
4. `TEXTUAL_BIO`: Bio, display name, and link mentions matched against city/province databases.
5. `TEMPORAL_TIMEZONE`: Inferred UTC offset from posting distribution hours (e.g., WIB, WITA, WIT).

### 3.3 `scorer.py` (Credibility Scoring Engine)
- Weights evidence by reliability:
  - EXIF GPS: base confidence 95%
  - Explicit Geotags: base confidence 85-90%
  - Visual AI / Landmarks: base confidence 75-85%
  - Bio / Textual: base confidence 70%
  - Temporal Timezone: base confidence 50%
- **Cluster Aggregation**: Groups candidates by city/region.
- **Cross-Validation Boost**: Grants a +10% to +25% confidence boost when multiple distinct signal types point to the same location.
- Obfuscates coordinates to city level (~0.05 deg) when `consent_mode` is `False`.

### 3.4 `audit.py` (Safety & Compliance Gate)
- SQLite database (`~/.delta/geotrace_audit.db` or configured path).
- Hash chain formula: `SHA-256(query_id + operator + target + timestamp + purpose + consent_mode + status + prev_record_hash)`.
- Enforces max 5 queries per target handle within a 1-hour window.
- Rejects private profiles (`REJECTED_PRIVATE`) and profiles with minor indicators (`REJECTED_MINOR`).
- Provides `verify_log_integrity()` to detect tampering.

### 3.5 `report.py` (Dual-Format Reporting)
- Generates machine-readable structured JSON (`GeoTraceResult`).
- Generates formatted executive summary in Markdown with an evidence matrix and legal disclaimer.

### 3.6 `vision_adapter.py` (Hybrid Vision)
- Accepts image URLs/paths; queries Delta's multimodal LLM when available.
- Falls back to heuristic landmark and plate-matching rules if LLM vision is offline.

---

## 4. Delta Tool Integration (`delta/ai/tools.py`)

Registers tool `geotrace_investigate`:
```python
Tool(
    name="geotrace_investigate",
    description="Perform OSINT geolocation investigation on a public social media account.",
    category="osint",
    func=geotrace_investigate_tool,
    parameters=[
        ToolParameter(name="target", type="string", description="Social media handle (e.g. @username) or public URL", required=True),
        ToolParameter(name="operator", type="string", description="Investigator/analyst identifier", required=False),
        ToolParameter(name="purpose", type="string", description="Legitimate reason for investigation (e.g., KYC, Incident Response)", required=True),
        ToolParameter(name="consent_mode", type="boolean", description="Whether subject explicitly granted consent for exact coordinates", required=False),
    ]
)
```

---

## 5. Web Server & UI Integration

### 5.1 Endpoints (`delta/web/server.py`)
- `POST /api/geotrace/analyze`: Runs analysis and returns JSON result.
- `GET /api/geotrace/audit`: Fetches audit log records.
- `POST /api/geotrace/verify-audit`: Runs SHA-256 hash-chain verification and returns integrity status.

### 5.2 UI / Sidebar (`delta/web/index.html` & `delta/web/static/index.html`)
- Sidebar item: **GeoTrace OSINT** with icon `location_on`.
- View panel with:
  - Target input form (Handle/URL, Purpose, Consent toggle).
  - Primary predicted location card (City, Region, Country, Confidence gauge).
  - Visual Evidence Matrix & Candidates Table.
  - Audit Trail Table with interactive "Verify Chain Integrity" trigger.

---

## 6. Compliance & Legal Framework (README.md)
- **UU PDP No. 27/2022 (Indonesia)**: Adherence to legitimate basis for processing, public data limitations, and purpose limitation.
- **GDPR (EU)**: Legitimate interest assessment, proportionality, right to explanation, and prohibition on unauthorized profiling.
- **Anti-Doxxing Policy**: Strict prohibition of precise residential coordinate publishing without consent.

---

## 7. Testing Strategy
- `tests/test_geotrace_scorer.py`: Unit test credibility calculation, cluster resolution, and cross-validation boosts.
- `tests/test_geotrace_extractor.py`: Unit test multi-source candidate extraction with mock EXIF, geotag, plate, and temporal inputs.
- `tests/test_geotrace_audit.py`: Unit test audit chain immutability, tamper detection, rate limiting, and ethical safety gate.
- `tests/test_geotrace_web.py`: Unit test Web API endpoints.
