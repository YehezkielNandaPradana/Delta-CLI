# GeoTrace: Ethical & OSINT Geolocation Intelligence Module

GeoTrace is a modular OSINT geolocation intelligence engine designed for legitimate security investigations (identity verification, threat intelligence, and incident response).

---

## 1. Ethical & Legal Boundaries

### Indonesia: UU PDP No. 27/2022 (Undang-Undang Perlindungan Data Pribadi)
1. **Public Data Processing**: Data processing is strictly limited to information made deliberately public by the data subject (Pasal 20 & Pasal 21).
2. **Purpose Limitation & Proportionality**: Collection and analysis are restricted to legitimate security research, verification (e.g. KYC), and defense purposes.
3. **Anti-Doxxing Safeguard**: Coordinate resolution is automatically quantized to ~5 km city-level radius when `consent_mode=False` to prevent unauthorized disclosure of residential addresses.
4. **Minor Protection**: Queries against accounts containing indicators of minors (<18 years old) are automatically refused by the safety gate.

### European Union: GDPR (General Data Protection Regulation)
1. **Article 6(1)(f) (Legitimate Interests)**: Balancing test applied to ensure investigative necessity outweighs intrusive processing.
2. **Account Access Boundaries**: No private profile scraping, no credential brute-forcing, and no bypass of platform access controls.

---

## 2. Multi-Vector Geolocation Architecture

```text
Public Footprint -> Collector -> Multi-Vector Extractor -> Credibility Scorer -> Report & Immutable Audit
```

- **EXIF GPS Metadata**: Extracted from camera metadata when published.
- **Explicit Geotags**: Check-in tags and place names.
- **Visual Clues (AI Vision & OCR)**: Landmarks, vehicle license plates (e.g. `B`, `D`, `AB`), storefront signage.
- **Textual Context**: Bio text, links, and local terminology.
- **Temporal Patterns**: Post timestamp distribution mapped to timezone offsets (WIB, WITA, WIT).

---

## 3. Cryptographic Audit Logging
All investigations are logged to an append-only SQLite database with SHA-256 hash chaining:
$$\text{Record Hash} = \text{SHA256}(\text{QueryID} : \text{Operator} : \text{Target} : \text{Timestamp} : \text{Purpose} : \text{Consent} : \text{Status} : \text{PrevHash})$$
Tampering with any historical audit log entry invalidates the chain integrity check.
