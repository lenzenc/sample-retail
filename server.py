def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Sample Retail API",
        version="1.0.0",
        description="Sample retail API with items and orders",
        routes=app.routes,
    )
    app.openapi_schema = openapi_schema
    return app.openapi_schema

# ... existing code ...

@app.get("/openapi.yaml", include_in_schema=False)
async def get_openapi_yaml():
    return Response(
        yaml.dump(app.openapi()),
        media_type="text/yaml"
    )

# Uncomment and update the docs endpoint
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url="/openapi.json",  # Change this from yaml to json
        title="API Docs"
    )