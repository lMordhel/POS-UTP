# Desplegar el POS-UTP en una VM gratuita

Objetivo: los dos servicios y Postgres corriendo en un host **que no duerme**, con
HTTPS de verdad, para que el front de Vercel pueda hablarles sin que el navegador
bloquee la petición.

**Por qué una VM y no un PaaS free**: los PaaS gratuitos (Render, Koyeb) duermen el
servicio por inactividad. El primer request despierta *sales*, que llama a *stock*
—también dormido— y `SALES_STOCK_TIMEOUT_SECONDS=5.0` corta la venta antes de que
termine de arrancar: el usuario ve un 502 y la saga compensa. Una VM no duerme.

**Por qué Caddy**: el front en Vercel se sirve por HTTPS y el navegador **bloquea**
que una página HTTPS llame a `http://IP:8001` (mixed content). El login fallaría en
la consola. Caddy pone TLS automático (Let's Encrypt) delante de los dos servicios
y no hay que comprar dominio: [sslip.io](https://sslip.io) resuelve cualquier IP.

```
Internet ──443──> Caddy ──> sales:8001
                    └─────> stock:8002
```

---

## 1. Crear la VM

### Opción recomendada: Oracle Cloud Always Free

- Instancia **Ampere A1 (ARM)**, Ubuntu 24.04, 2 OCPU / 12 GB alcanza de sobra.
  El Always Free permite hasta 4 OCPU / 24 GB: pedí de menos, no más.
- Oracle pide tarjeta para verificar identidad; el Always Free no cobra.
- **Si la creación falla con "out of capacity"**: es lo normal en ARM. Probá otra
  zona de disponibilidad, otro shape (VM.Standard.E2.1.Micro, x86, también free) o
  insistí otro día. No es un error tuyo.

### Alternativa: Google Cloud e2-micro (always free)

- `e2-micro` en `us-central1`, `us-west1` o `us-east1`, 30 GB de disco.
- Solo 1 GB de RAM: los dos servicios FastAPI + Postgres + Caddy entran, pero
  ajustado. Si ves el OOM killer en `dmesg`, mové Postgres a Neon y dejá la VM
  solo para los servicios.
- La IP estática tiene costo; para una demo alcanza la efímera, pero **si cambia,
  cambian los hostnames y el certificado**. Reservala si podés.

## 2. Preparar el sistema

```bash
ssh ubuntu@<IP_PUBLICA>          # en GCP el usuario es el que creaste

sudo apt-get update
sudo apt-get install -y ca-certificates curl git
# Docker oficial (el de apt suele estar viejo)
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] \
https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo $VERSION_CODENAME) stable" \
  | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
sudo usermod -aG docker $USER && newgrp docker
```

## 3. Abrir los puertos (acá se cae todo el mundo)

### Oracle: **dos** firewalls, no uno

1. **Security List de la VCN** (consola): ingress TCP `22`, `80`, `443` desde
   `0.0.0.0/0`.
2. **iptables dentro de la VM**: las imágenes de Oracle traen una regla que
   rechaza todo salvo el 22, y **no alcanza con abrir la Security List**. Sí o sí:

```bash
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 443 -j ACCEPT
sudo netfilter-persistent save    # si no está: apt install iptables-persistent
```

Sin esto, Caddy no puede validar el dominio por HTTP-01 y el certificado no se
emite: vas a ver el sitio sin HTTPS y un error de ACME en los logs.

### GCP: regla de firewall

```bash
gcloud compute firewall-rules create pos-web \
  --allow tcp:22,tcp:80,tcp:443 --source-ranges 0.0.0.0/0
```

**No abras 8001 ni 8002.** Caddy llega a los servicios por la red interna de
Docker; publicarlos al mundo solo agrega superficie sin TLS.
Ojo: los puertos que publique Docker se saltan `ufw` por cómo inserta sus reglas
en iptables. Si querés cerrarlos, no los agregues a la Security List / firewall
del proveedor.

## 4. Traer el código

```bash
git clone git@github.com:lMordhel/POS-UTP.git    # o HTTPS con un PAT
cd POS-UTP
```

En una VM conviene una **deploy key** de solo lectura: Settings → Deploy keys →
`ssh-keygen -t ed25519` en la VM y pegás la pública.

## 5. Crear `infra/.env`

No se versiona (está en `.gitignore`) y contiene los secretos. En la VM:

```bash
cd infra
cat > .env <<'EOF'
# Despliegue en VM. NO versionar.
POS_ENV=prod
POS_LOG_LEVEL=INFO

# Un solo secreto para los dos servicios: Sales firma el token de servicio que
# Stock verifica (ADR-008). DOS VALORES DISTINTOS ROMPEN LA SAGA.
JWT_SECRET=<pegar aca la salida de: openssl rand -hex 32>
ADMIN_PASSWORD=<elegir una password real, no change-me-admin>

# Dominio del front en Vercel. Sin barra final. Si despues agregas un dominio
# propio, sumalo separado por coma: https://a.vercel.app,https://midominio.com
CORS_ORIGINS=https://<tu-app>.vercel.app

# Hostnames publicos de los servicios. Con sslip.io no hace falta dominio:
# 203.0.113.5  ->  sales.203-0-113-5.sslip.io
SALES_HOST=sales.<IP-CON-GUIONES>.sslip.io
STOCK_HOST=stock.<IP-CON-GUIONES>.sslip.io
EOF
chmod 600 .env
```

> `POS_ENV=prod` desactiva `/docs` y hace **fallar el arranque** si quedan los
> secretos de ejemplo. Es a propósito: si el contenedor no levanta, revisá este
> archivo primero.

## 6. Levantar el stack

```bash
cd /home/ubuntu/POS-UTP          # o donde hayas clonado
docker compose \
  -f infra/docker-compose.yml \
  -f infra/docker-compose.prod.yml \
  up -d --build
```

Compose carga `infra/.env` solo cuando el proyecto es esa carpeta; con `-f infra/...`
el proyecto es `infra/`, así que lo toma. Verificá que no falte nada:

```bash
docker compose -f infra/docker-compose.yml -f infra/docker-compose.prod.yml config | head -40
```

## 7. Migraciones

Se corren **una vez**, dentro del contenedor (Alembic lee `DATABASE_URL` de la
config del servicio, así que ya ve el Postgres del compose):

```bash
docker compose -f infra/docker-compose.yml -f infra/docker-compose.prod.yml exec sales alembic upgrade head
docker compose -f infra/docker-compose.yml -f infra/docker-compose.prod.yml exec stock alembic upgrade head
```

## 8. Verificar

```bash
curl -sS https://$SALES_HOST/health    # {"status":"ok"}
curl -sS https://$STOCK_HOST/health
curl -sS -o /dev/null -w '%{http_code}\n' https://$SALES_HOST/docs   # 404: POS_ENV=prod lo desactiva
```

El certificado puede tardar uno o dos minutos la primera vez:

```bash
docker compose -f infra/docker-compose.yml -f infra/docker-compose.prod.yml logs caddy | tail -20
```

## 9. Apuntar Vercel al back

En Vercel → Settings → Environment Variables (Production y Preview):

```
VITE_SALES_URL = https://sales.<IP-CON-GUIONES>.sslip.io
VITE_STOCK_URL = https://stock.<IP-CON-GUIONES>.sslip.io
```

Después **Redeploy**: las `VITE_*` se hornean al compilar, no se leen en runtime.

Y `CORS_ORIGINS` en `infra/.env` tiene que incluir el dominio exacto del front,
sin barra final. Si el dominio no coincide, el navegador bloquea y la consola dice
`blocked by CORS policy`.

## 10. Que sobreviva a un reinicio

El overlay ya trae `restart: unless-stopped`, así que los contenedores vuelven
solos. Solo asegurate de que el demonio de Docker arranque con el sistema:

```bash
sudo systemctl enable docker
```

---

## Problemas típicos

| Síntoma | Causa | Solución |
|---|---|---|
| El certificado nunca se emite, ACME falla por HTTP-01 | El 80 no llega a la VM | Security List **y** iptables (paso 3) |
| El login falla con `blocked by CORS policy` | `CORS_ORIGINS` no coincide con el dominio del front | Mismo dominio, sin barra final, y redeploy del back |
| El login falla con error de *mixed content* | Las `VITE_*` apuntan a `http://` | Usar las URLs `https://` de Caddy y redeployar el front |
| `sales` no levanta y el log habla de secretos | `POS_ENV=prod` con secretos de ejemplo | `JWT_SECRET` y `ADMIN_PASSWORD` reales en `infra/.env` |
| 502 en una venta | Stock caído o lento | `docker compose ps` y `logs stock`; el timeout del cliente es 5 s |
| Todo anda y al día siguiente no | Reboot sin `restart` o sin `systemctl enable docker` | Paso 10 |
| Oracle: "out of capacity" al crear la VM ARM | Sin capacidad en esa zona | Otra AD, shape x86 Micro, u otro día |

## Costo y límites

- Oracle Always Free: VM ARM hasta 4 OCPU / 24 GB y 200 GB de bloque, sin vencer.
  No cobra si no salís del tier.
- GCP e2-micro: 1 instancia always free por mes en las regiones listadas; la IP
  estática se cobra.
- Let's Encrypt vía Caddy es gratis y se renueva solo, pero depende de que el 80
  siga abierto: **no lo cierres después de emitir el certificado**.
