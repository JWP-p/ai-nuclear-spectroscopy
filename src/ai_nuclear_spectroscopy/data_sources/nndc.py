"""Small, provenance-first NNDC ENSDF retrieval client.

The client downloads data only when explicitly invoked. Upstream HTML, PDFs,
and database snapshots are not vendored in this repository. Callers are
responsible for following NNDC citation guidance for the exact data they use.
"""

from __future__ import annotations

import hashlib
import html
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime

SEARCH_URL = "https://www.nndc.bnl.gov/ensdf/DatasetFetchServlet"
DISPATCH_URL = "https://www.nndc.bnl.gov/ensdf/EnsdfDispatcherServlet"
USER_AGENT = "ai-nuclear-spectroscopy/0.1 (open research workflow)"
ROW_RE = re.compile(
    r'<tr>\s*.*?name="datasetcheck"\s+value="([^"]+)">(.*?)</input>\s*</td>\s*<td>(.*?)</td>',
    re.IGNORECASE | re.DOTALL,
)
PRE_RE = re.compile(r"<pre>(.*?)</pre>", re.IGNORECASE | re.DOTALL)


class RetrievalError(RuntimeError):
    """Raised when an upstream response is unavailable or structurally invalid."""


@dataclass(frozen=True)
class DatasetReference:
    source: str
    datasetcheck: str
    record_id: str
    nucleus: str
    title: str
    revision: str


@dataclass(frozen=True)
class RetrievalManifest:
    schema: str
    source_name: str
    source_url: str
    retrieved_utc: str
    content_type: str
    byte_count: int
    sha256: str
    citation_note: str
    dataset_references: tuple[dict[str, str], ...]


def _clean_markup(value: str) -> str:
    return " ".join(html.unescape(re.sub(r"<[^>]+>", "", value)).split())


def _normalize_nucleus(value: str) -> str:
    match = re.fullmatch(r"\s*(\d+)\s*([A-Za-z]+)\s*", value)
    if not match:
        raise RetrievalError(f"Invalid nucleus label returned by NNDC: {value!r}")
    return f"{int(match.group(1))}{match.group(2).title()}"


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


class NndcEnsdfClient:
    """Retrieve public ENSDF/XUNDL records with a dated manifest."""

    def __init__(self, *, timeout_seconds: int = 90, retries: int = 3) -> None:
        if timeout_seconds <= 0 or retries <= 0:
            raise ValueError("timeout_seconds and retries must be positive")
        self.timeout_seconds = timeout_seconds
        self.retries = retries

    def _request(
        self,
        url: str,
        fields: Iterable[tuple[str, str]] | None = None,
    ) -> tuple[bytes, str]:
        body = urllib.parse.urlencode(list(fields or [])).encode("utf-8") if fields else None
        headers = {"User-Agent": USER_AGENT}
        if body is not None:
            headers["Content-Type"] = "application/x-www-form-urlencoded"
        last_error: Exception | None = None
        for attempt in range(self.retries):
            try:
                request = urllib.request.Request(url, data=body, headers=headers)
                with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                    payload = response.read()
                    content_type = response.headers.get("Content-Type", "")
                if not payload:
                    raise RetrievalError(f"Empty response from {url}")
                return payload, content_type
            except (OSError, TimeoutError, urllib.error.URLError, RetrievalError) as error:
                last_error = error
                if attempt + 1 < self.retries:
                    time.sleep(0.5 * (attempt + 1))
        raise RetrievalError(f"NNDC request failed after {self.retries} attempts: {last_error}")

    def search(self, nucleus_or_element: str, *, source: str = "ensdf") -> list[DatasetReference]:
        """Return NNDC dataset identifiers without downloading dataset payloads."""
        source = source.lower()
        if source not in {"ensdf", "xundl"}:
            raise ValueError("source must be 'ensdf' or 'xundl'")
        payload, content_type = self._request(
            SEARCH_URL,
            [
                ("nuc", nucleus_or_element),
                ("searchType", "quick"),
                ("datasource", source),
            ],
        )
        if "html" not in content_type.lower():
            raise RetrievalError(f"Unexpected NNDC search content type: {content_type}")
        page = payload.decode("utf-8", errors="replace")
        references: list[DatasetReference] = []
        for datasetcheck, raw_title, raw_revision in ROW_RE.findall(page):
            try:
                record_id, raw_nucleus = datasetcheck.split(",", 1)
            except ValueError as error:
                raise RetrievalError(
                    f"Malformed NNDC dataset identifier: {datasetcheck}"
                ) from error
            references.append(
                DatasetReference(
                    source=source,
                    datasetcheck=datasetcheck,
                    record_id=record_id,
                    nucleus=_normalize_nucleus(raw_nucleus),
                    title=_clean_markup(raw_title),
                    revision=_clean_markup(raw_revision),
                )
            )
        if not references:
            raise RetrievalError("No dataset references were found in the NNDC response")
        if len({row.datasetcheck for row in references}) != len(references):
            raise RetrievalError("NNDC search response contained duplicate dataset identifiers")
        return references

    def fetch_ensdf_text(
        self,
        references: Iterable[DatasetReference],
    ) -> tuple[str, RetrievalManifest]:
        """Download selected references in ENSDF text format and record provenance."""
        rows = tuple(references)
        if not rows:
            raise ValueError("At least one dataset reference is required")
        sources = {row.source for row in rows}
        if len(sources) != 1:
            raise ValueError("A dispatcher request must use one source database")
        fields: list[tuple[str, str]] = [
            ("dbclass", rows[0].source),
            ("page-source", "singular"),
        ]
        fields.extend(("datasetcheck", row.datasetcheck) for row in rows)
        fields.append(("chooseit", "ENSDF text format"))
        payload, content_type = self._request(DISPATCH_URL, fields)
        if "html" not in content_type.lower():
            raise RetrievalError(f"Unexpected NNDC dispatcher content type: {content_type}")
        page = payload.decode("utf-8", errors="replace")
        match = PRE_RE.search(page)
        if not match:
            raise RetrievalError("NNDC dispatcher response did not contain an ENSDF text block")
        text = html.unescape(match.group(1)).replace("\r\n", "\n").replace("\r", "\n")
        text = text.strip("\n") + "\n"
        encoded = text.encode("latin-1", errors="replace")
        manifest = RetrievalManifest(
            schema="nndc_retrieval_manifest_v1",
            source_name=f"NNDC {rows[0].source.upper()}",
            source_url=DISPATCH_URL,
            retrieved_utc=datetime.now(UTC).isoformat(),
            content_type="text/plain; charset=latin-1",
            byte_count=len(encoded),
            sha256=_sha256(encoded),
            citation_note=(
                "Cite the individual evaluation or the dated ENSDF database version "
                "according to NNDC guidance."
            ),
            dataset_references=tuple(asdict(row) for row in rows),
        )
        return text, manifest
