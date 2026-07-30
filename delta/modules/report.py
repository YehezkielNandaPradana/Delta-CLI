# delta/modules/report.py
"""
Report Module - Generates professional security reports in Markdown, HTML, and JSON formats.
"""

import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class ReportData:
    """Data structure for report generation."""
    title: str = "Delta Security Assessment Report"
    company: str = "Delta Security"
    author: str = "Delta Analyst"
    target: str = ""
    scan_date: str = ""
    duration: float = 0.0
    risk_level: str = "info"
    summary: str = ""
    findings: List[Dict] = field(default_factory=list)
    recommendations: List[Dict] = field(default_factory=list)
    host_info: Dict[str, Any] = field(default_factory=dict)
    open_ports: List[Dict] = field(default_factory=list)
    services: Dict[str, Any] = field(default_factory=dict)
    vulnerabilities: List[Dict] = field(default_factory=list)


class ReportModule:
    """
    Professional report generator for security assessments.
    Supports Markdown, HTML, and JSON output formats.
    """

    SUPPORTED_FORMATS = ("markdown", "md", "html", "json", "all")

    def generate(self, data: ReportData, output_dir: str = "reports", format: str = "all") -> Dict[str, str]:
        """Generate reports in specified format(s)."""
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = f"delta_report_{data.target.replace('.', '_')}_{timestamp}"
        
        generated = {}
        
        if format in ("markdown", "md", "all"):
            md_path = os.path.join(output_dir, f"{base_name}.md")
            self._save_report(md_path, self._generate_markdown(data))
            generated["markdown"] = md_path
        
        if format in ("html", "all"):
            html_path = os.path.join(output_dir, f"{base_name}.html")
            self._save_report(html_path, self._generate_html(data))
            generated["html"] = html_path
        
        if format in ("json", "all"):
            json_path = os.path.join(output_dir, f"{base_name}.json")
            self._save_report(json_path, self._generate_json(data))
            generated["json"] = json_path
        
        return generated

    def _save_report(self, path: str, content: str) -> None:
        """Save report content to file."""
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

    def _generate_markdown(self, data: ReportData) -> str:
        """Generate Markdown report."""
        md = []
        md.append(f"# {data.title}")
        md.append(f"")
        md.append(f"**Company:** {data.company}  ")
        md.append(f"**Author:** {data.author}  ")
        md.append(f"**Target:** {data.target}  ")
        md.append(f"**Scan Date:** {data.scan_date}  ")
        md.append(f"**Duration:** {data.duration:.2f}s  ")
        md.append(f"**Risk Level:** {data.risk_level.upper()}  ")
        md.append("")
        md.append("---")
        md.append("")
        
        # Executive Summary
        md.append("## Executive Summary")
        md.append("")
        md.append(data.summary or "No summary available.")
        md.append("")
        
        # Host Information
        md.append("## Host Information")
        md.append("")
        md.append("| Field | Value |")
        md.append("|-------|-------|")
        if data.host_info:
            for key, value in data.host_info.items():
                md.append(f"| {key} | {value} |")
        md.append("")
        
        # Open Ports
        if data.open_ports:
            md.append("## Open Ports")
            md.append("")
            md.append("| Port | Service | State |")
            md.append("|------|---------|-------|")
            for port in data.open_ports:
                md.append(f"| {port.get('port', '')} | {port.get('service', '')} | {port.get('state', '')} |")
            md.append("")
        
        # Findings
        if data.findings:
            md.append("## Security Findings")
            md.append("")
            for i, finding in enumerate(data.findings, 1):
                severity = finding.get("severity", "info").upper()
                md.append(f"### Finding {i}: {finding.get('title', '')}")
                md.append(f"")
                md.append(f"**Severity:** {severity}  ")
                md.append(f"**Description:** {finding.get('description', '')}  ")
                md.append(f"**Evidence:** {finding.get('evidence', '')}  ")
                md.append(f"**Recommendation:** {finding.get('recommendation', '')}  ")
                md.append("")
        
        # Recommendations
        if data.recommendations:
            md.append("## Recommendations")
            md.append("")
            for i, rec in enumerate(data.recommendations, 1):
                md.append(f"{i}. **{rec.get('title', '')}** ({rec.get('severity', '').upper()})")
                md.append(f"   - {rec.get('remediation', '')}")
            md.append("")
        
        # Conclusion
        md.append("## Conclusion")
        md.append("")
        md.append(f"This security assessment of **{data.target}** identified a risk level of **{data.risk_level.upper()}**.")
        md.append(f"Total findings: {len(data.findings)}")
        md.append("")
        md.append("---")
        md.append(f"*Report generated by Delta Security Assessment CLI*")
        
        return "\n".join(md)

    def _generate_html(self, data: ReportData) -> str:
        """Generate HTML report."""
        severity_colors = {
            "critical": "#dc3545",
            "high": "#fd7e14",
            "medium": "#ffc107",
            "low": "#17a2b8",
            "info": "#6c757d",
        }
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{data.title} - {data.target}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; background: #f8f9fa; }}
        .container {{ max-width: 900px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; margin-bottom: 20px; }}
        .header h1 {{ font-size: 2em; margin-bottom: 10px; }}
        .risk-level {{ display: inline-block; padding: 5px 15px; border-radius: 20px; font-weight: bold; font-size: 1.2em; background: {severity_colors.get(data.risk_level.lower(), '#6c757d')}; color: white; }}
        .section {{ background: white; padding: 20px; border-radius: 8px; margin-bottom: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .section h2 {{ color: #495057; border-bottom: 2px solid #667eea; padding-bottom: 10px; margin-bottom: 15px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
        th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #dee2e6; }}
        th {{ background: #f1f3f5; font-weight: 600; }}
        .finding {{ border-left: 4px solid #667eea; padding: 15px; margin: 10px 0; background: #f8f9fa; border-radius: 4px; }}
        .finding.critical {{ border-left-color: #dc3545; }}
        .finding.high {{ border-left-color: #fd7e14; }}
        .finding.medium {{ border-left-color: #ffc107; }}
        .finding.low {{ border-left-color: #17a2b8; }}
        .severity-badge {{ display: inline-block; padding: 2px 8px; border-radius: 10px; font-size: 0.8em; font-weight: bold; color: white; }}
        .footer {{ text-align: center; color: #6c757d; padding: 20px; font-size: 0.9em; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{data.title}</h1>
            <p>Target: <strong>{data.target}</strong></p>
            <p>Date: {data.scan_date} | Duration: {data.duration:.2f}s</p>
            <p class="risk-level">Risk Level: {data.risk_level.upper()}</p>
        </div>
        
        <div class="section">
            <h2>Executive Summary</h2>
            <p>{data.summary or "No summary available."}</p>
        </div>
        
        <div class="section">
            <h2>Host Information</h2>
            <table>
                <tr><th>Field</th><th>Value</th></tr>"""
        
        if data.host_info:
            for key, value in data.host_info.items():
                html += f"<tr><td>{key}</td><td>{value}</td></tr>\n"
        
        html += """</table>
        </div>"""
        
        if data.open_ports:
            html += """
        <div class="section">
            <h2>Open Ports</h2>
            <table>
                <tr><th>Port</th><th>Service</th><th>State</th></tr>"""
            for port in data.open_ports:
                html += f"<tr><td>{port.get('port', '')}</td><td>{port.get('service', '')}</td><td>{port.get('state', '')}</td></tr>\n"
            html += "</table></div>"
        
        if data.findings:
            html += """
        <div class="section">
            <h2>Security Findings</h2>"""
            for finding in data.findings:
                severity = finding.get("severity", "info").lower()
                color = severity_colors.get(severity, "#6c757d")
                html += f"""
            <div class="finding {severity}">
                <h3>{finding.get('title', '')}</h3>
                <p><span class="severity-badge" style="background: {color};">{severity.upper()}</span></p>
                <p><strong>Description:</strong> {finding.get('description', '')}</p>
                <p><strong>Evidence:</strong> {finding.get('evidence', '')}</p>
                <p><strong>Recommendation:</strong> {finding.get('recommendation', '')}</p>
            </div>"""
            html += "</div>"
        
        if data.recommendations:
            html += """
        <div class="section">
            <h2>Recommendations</h2>
            <ol>"""
            for rec in data.recommendations:
                severity = rec.get("severity", "info").upper()
                html += f"<li><strong>{rec.get('title', '')}</strong> ({severity})<br>{rec.get('remediation', '')}</li>"
            html += "</ol></div>"
        
        html += f"""
        <div class="section">
            <h2>Conclusion</h2>
            <p>This security assessment of <strong>{data.target}</strong> identified a risk level of <strong>{data.risk_level.upper()}</strong>.</p>
            <p>Total findings: {len(data.findings)}</p>
        </div>
        
        <div class="footer">
            <p>Report generated by Delta Security Assessment CLI | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
    </div>
</body>
</html>"""
        
        return html

    def _generate_json(self, data: ReportData) -> str:
        """Generate JSON report."""
        report = {
            "report_metadata": {
                "title": data.title,
                "company": data.company,
                "author": data.author,
                "generated_at": datetime.now().isoformat(),
                "tool": "Delta Security Assessment CLI v1.0",
            },
            "scan_info": {
                "target": data.target,
                "scan_date": data.scan_date,
                "duration_seconds": data.duration,
                "risk_level": data.risk_level,
            },
            "executive_summary": data.summary,
            "host_information": data.host_info,
            "open_ports": data.open_ports,
            "findings": data.findings,
            "recommendations": data.recommendations,
            "finding_summary": {
                "total": len(data.findings) + len(data.vulnerabilities),
                "critical": sum(1 for f in data.findings if f.get("severity", "").lower() == "critical"),
                "high": sum(1 for f in data.findings if f.get("severity", "").lower() == "high"),
                "medium": sum(1 for f in data.findings if f.get("severity", "").lower() == "medium"),
                "low": sum(1 for f in data.findings if f.get("severity", "").lower() == "low"),
            }
        }
        return json.dumps(report, indent=2)