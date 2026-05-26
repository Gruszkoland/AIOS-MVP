"""Contract tests for Arbitrage API against OpenAPI schema.

Validates that all API responses conform to documented OpenAPI 3.1 spec.
Uses Schemathesis for property-based API testing against schema.
"""
import pytest
import schemathesis

# Load OpenAPI spec
spec = schemathesis.from_path("docs/openapi.yaml")


@pytest.mark.contract
@spec.parametrize()
def test_api_response_conforms_to_schema(case):
    """Property-based test: every response must match OpenAPI schema.

    Schemathesis generates test cases from schema, executes them,
    and validates responses against the documented schema.
    """
    response = case.call_and_validate()
    # If response doesn't match schema, schemathesis raises ValidationError
    assert response.status_code in case.operation.responses
