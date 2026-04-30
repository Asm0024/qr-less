# QRLess

QRLess is a small full-stack app for creating QR codes.

- Frontend: React + Vite in `web/`
- Backend: Flask in `generator/src/`
- Deploy: Serverless Framework to AWS Lambda, API Gateway, DynamoDB, S3, and CloudFront

## Run Locally

Install everything once:

```sh
npm run install:all
```

Start the frontend and backend:

```sh
npm run dev
```

Open:

```txt
http://127.0.0.1:8080
```

Local mode uses in-memory users and QR history. Data resets when the backend stops. If the S3 upload toggle is on locally, the backend saves the image into `generator/local_uploads/` and returns a localhost image URL.

## Run Tests

```sh
npm run test
```

The basic tests cover register, login, QR generation, and QR history.

## Deploy To AWS

Requirements:

- AWS credentials already configured
- Docker running
- Node.js, npm, and Python 3 installed

Start Docker Desktop before deploy. Check it with:

```sh
docker info
```

If Docker is not ready, deploy fails before AWS with a Python packaging error.

Configure AWS once if you have not done it yet:

1. Open the AWS Console.
2. Go to IAM.
3. Create or open an IAM user for deployments.
4. Give that user permissions to deploy this app. For a quick test, `AdministratorAccess` works, but for production use a smaller custom policy.
5. Open the user's `Security credentials` tab.
6. Click `Create access key`.
7. Choose `Command Line Interface (CLI)`.
8. Copy the `Access key ID` and `Secret access key`. The secret is shown only once.

AWS docs: https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_access-keys.html

Then run:

```sh
aws configure
```

Use these values:

```txt
AWS Access Key ID: <your-access-key>
AWS Secret Access Key: <your-secret-key>
Default region name: eu-central-1
Default output format: json
```

This tells Serverless which AWS account and region to deploy to.

Deploy:

```sh
SECRET_KEY="replace-this-with-a-long-random-secret" npm run deploy -- --stage dev
```

Only `SECRET_KEY` needs to be changed. Bucket names are already filled in:

- `qrless-qrcodes-monster-20260430-dev`
- `qrless-site-monster-20260430-dev`

After deploy, Serverless prints `SiteUrl`. Open that URL to use the deployed app.

## Remove From AWS

```sh
npm run remove -- --stage dev
```

If AWS refuses to delete the stack because the QR bucket has files in it, empty the bucket first.

## Backend Files

- `generator/src/app.py`: creates the Flask app and registers routes
- `generator/src/routes/auth_routes.py`: register, login, logout, user lookup
- `generator/src/routes/qr_routes.py`: QR generation and history
- `generator/src/storage.py`: local in-memory storage or AWS DynamoDB/S3
- `generator/src/security.py`: password hashing and JWT token checks
- `generator/serverless.yml`: AWS deployment
