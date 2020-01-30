# Seosnap Dashboard

```
cp .env.example .env
# Edit default settings

docker-compose up -d --build
```

## Updating Python requirements.txt
If you haven't got pip-compile installed yet:

```bash
pip3 install pip-tools
```

Then generate a new .txt file:

```bash
pip-compile requirements.in
```
Commit both files to version control.
