class ApiPrefixMiddleware:
    """Strip the CloudFront /api prefix before Flask handles the request.

    CloudFront forwards API requests as `/api/...`, but the Flask routes are
    registered as `/users`, `/generate`, and so on. This tiny WSGI middleware
    rewrites the incoming path before Flask tries to match it.
    """

    def __init__(self, app, prefix):
        # `app` is the next WSGI application in the chain; `prefix` is the
        # public URL segment that should not be part of Flask route matching.
        self.app = app
        self.prefix = prefix

    def __call__(self, environ, start_response):
        # WSGI stores the request path in PATH_INFO. Mutating it here changes
        # what Flask sees without changing the original browser URL.
        path = environ.get("PATH_INFO", "")
        if path == self.prefix:
            environ["PATH_INFO"] = "/"
        elif path.startswith(f"{self.prefix}/"):
            environ["PATH_INFO"] = path[len(self.prefix) :]

        # Continue request handling with Flask after the path has been adjusted.
        return self.app(environ, start_response)
