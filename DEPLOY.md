# Deploy — Portal ESTVP Atauro

Production stack from `PLAN.md`: **Ubuntu LTS + Nginx + Gunicorn + PostgreSQL**.

Local development stays on `python manage.py runserver 127.0.0.1:8001`.

## 1. Server packages

```bash
sudo apt update
sudo apt install -y python3-venv python3-pip postgresql nginx
```

Create the database and a dedicated role (do not use the postgres superuser in production).

## 2. Application

```bash
sudo mkdir -p /var/www/portal_eskola
sudo chown "$USER":www-data /var/www/portal_eskola
git clone <repo-url> /var/www/portal_eskola
cd /var/www/portal_eskola
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env`:

- `DEBUG=False`
- strong `SECRET_KEY` (40+ random characters)
- `ALLOWED_HOSTS` = public hostname
- real `DB_*` values
- `SESSION_COOKIE_SECURE=True`
- `CSRF_COOKIE_SECURE=True`
- `SECURE_SSL_REDIRECT=True`
- `CSRF_TRUSTED_ORIGINS=https://your-domain`

```bash
python manage.py migrate
python manage.py setup_roles
python manage.py collectstatic --noinput
python manage.py check_deploy
python manage.py createsuperuser
```

Media directory must be writable by the Gunicorn user (`www-data`).

## 3. Gunicorn

Example unit: `deploy/portal-eskola.service`.

```bash
sudo cp deploy/portal-eskola.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now portal-eskola
sudo systemctl status portal-eskola
```

Gunicorn listens on `127.0.0.1:8001` (`deploy/gunicorn.conf.py`).

## 4. Nginx

```bash
sudo cp deploy/nginx.conf.example /etc/nginx/sites-available/portal-eskola
# edit server_name and paths
sudo ln -s /etc/nginx/sites-available/portal-eskola /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

HTTPS (after DNS points to the server):

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d escola.example.tl
```

## 5. Backup

On the server, install `postgresql-client` and run the same procedures documented in `README.md`:

- `scripts/backup.ps1` / `scripts/restore.ps1` on Windows admin machines, or
- `pg_dump` / `pg_restore` plus a zip of `media/` on Ubuntu.

Verify a restore on a staging copy before relying on backups.

## 6. Checklist

```bash
python manage.py check_deploy
sudo systemctl status portal-eskola nginx postgresql
curl -I http://127.0.0.1:8001/
```
