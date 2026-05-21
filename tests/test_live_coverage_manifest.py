from aiograpi_rest.main import app
from tests.live.coverage_manifest import guarded_operations, operation_policy


def _openapi_operations() -> set[tuple[str, str]]:
    return {
        (method.upper(), path)
        for path, methods in app.openapi()["paths"].items()
        for method in methods
    }


def test_live_coverage_manifest_classifies_every_openapi_operation():
    missing = [
        f"{method} {path}"
        for method, path in sorted(_openapi_operations())
        if operation_policy(method, path).kind == "unclassified"
    ]

    assert missing == []


def test_live_coverage_manifest_requires_post_mutation_verification():
    missing_verification = []
    for method, path in sorted(_openapi_operations()):
        policy = operation_policy(method, path)
        if method in {"POST", "PATCH", "DELETE"} and policy.kind != "guarded":
            if not policy.verify_with:
                missing_verification.append(f"{method} {path}")

    assert missing_verification == []


def test_live_coverage_manifest_documents_guarded_operations():
    guarded = guarded_operations()

    assert ("PATCH", "/account/password") in guarded
    assert ("POST", "/auth/challenge/resolve") in guarded
    assert all(policy.reason for policy in guarded.values())


def test_live_coverage_manifest_covers_uploaded_media_edit_and_delete():
    assert operation_policy("PATCH", "/media").kind != "guarded"
    assert operation_policy("PATCH", "/media").verify_with == "GET /media"
    assert operation_policy("DELETE", "/media").kind != "guarded"
    assert operation_policy("DELETE", "/media").verify_with == "GET /media returns 404 or missing media"
