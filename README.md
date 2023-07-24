# proxy-server

Inference Proxy Server

Run `gcloud run deploy` to deploy the Docker container to production.

Run locally with `docker build -t proxy_server . && docker run -v ~/.config:/root/.config -t -p 8080:8080 proxy_server`.

The `-v ~/.config:/root/.config` flag is required to allow the container to access the default Google Cloud credentials when you are running on your local machine. If you don't have these setup, do so with `gcloud auth application-default login`.

The container also depends on a Cloud SQL instance.
