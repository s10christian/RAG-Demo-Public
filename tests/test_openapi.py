from app.main import app


def test_openapi_documents_bearer_authentication():
    schema = app.openapi()
    assert schema["components"]["securitySchemes"]["BearerAuth"]["scheme"] == "bearer"
    assert schema["paths"]["/api/v1/query"]["post"]["security"] == [{"BearerAuth": []}]
    assert schema["paths"]["/api/v1/documents/text"]["post"]["security"] == [{"BearerAuth": []}]
