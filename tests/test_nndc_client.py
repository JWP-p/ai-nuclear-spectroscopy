from ai_nuclear_spectroscopy.data_sources.nndc import NndcEnsdfClient


def test_nndc_search_metadata_parser_without_network() -> None:
    client = NndcEnsdfClient()
    page = (
        b'<table><tr><td><input name="datasetcheck" value="12345,100Mo">'
        b"X</input></td><td>ADOPTED LEVELS</td></tr></table>"
    )
    client._request = lambda url, fields=None: (page, "text/html")  # type: ignore[method-assign]
    rows = client.search("100Mo")
    assert len(rows) == 1
    assert rows[0].nucleus == "100Mo"
    assert rows[0].record_id == "12345"


def test_nndc_dispatcher_extracts_text_and_manifest_without_network() -> None:
    client = NndcEnsdfClient()
    search_page = (
        b'<tr><td><input name="datasetcheck" value="12345,100Mo">'
        b"X</input></td><td>ADOPTED LEVELS</td></tr>"
    )
    client._request = lambda url, fields=None: (search_page, "text/html")  # type: ignore[method-assign]
    reference = client.search("100Mo")[0]
    response = b"<html><pre>100MO    ADOPTED LEVELS\n</pre></html>"
    client._request = lambda url, fields=None: (response, "text/html")  # type: ignore[method-assign]
    text, manifest = client.fetch_ensdf_text([reference])
    assert text.startswith("100MO")
    assert manifest.byte_count > 0
    assert len(manifest.sha256) == 64
