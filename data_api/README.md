- Start the API locally with 

```
uv run uvicorn data_api.app:app --reload --port 8000
```

- Curl

```
curl 127.0.0.1:8000
```

- Generate an API token and then add it to the .env/modal secrets under ``ZWIFT_DS_API_TOKEN``

```
openssl rand -hex 32
```