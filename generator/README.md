# Backend

The main project README has the local and AWS deploy instructions.

Backend code lives in `src/`:

- `src/app.py` creates the Flask app
- `src/routes/auth_routes.py` has auth endpoints
- `src/routes/qr_routes.py` has QR endpoints
- `src/storage.py` switches between local memory and AWS DynamoDB/S3
- `serverless.yml` deploys the full stack
