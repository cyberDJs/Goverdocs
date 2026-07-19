from goverdocs.classifier import classify


def test_security_classification() -> None:
    names = {event.name for event in classify(["src/auth/token.py"], "authorization policy")}
    assert "security_boundary_change" in names
    assert "authentication_authorization_change" in names


def test_dependency_classification() -> None:
    assert {event.name for event in classify(["pyproject.toml"])} == {"dependency_change"}


def test_document_classification() -> None:
    names = {event.name for event in classify(["docs/architecture/system.md"])}
    assert {"architecture_change", "document_changed"}.issubset(names)
