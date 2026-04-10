# 04 - Labs Practicos (hands-on)

## Requisitos
- 1 VM Linux (Ubuntu Server recomendado).
- Herramientas: `openssl`, `nmap`, `tcpdump`, `dig`, `curl`, `jq`.
- Permisos de administrador sobre tu laboratorio.

## Lab 1: Inspeccion de handshake TLS
### Objetivo
Confirmar version TLS y ciphers negociados.

### Pasos
```bash
openssl s_client -connect ejemplo.com:443 -tls1_3
nmap --script ssl-enum-ciphers -p 443 ejemplo.com
```

### Criterio de exito
- El servidor soporta TLS moderno.
- No aparecen suites debiles obsoletas.

---

## Lab 2: Hardening SSH real
### Objetivo
Bloquear vectores comunes de brute force.

### Pasos
1. Editar `/etc/ssh/sshd_config`:
```text
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
MaxAuthTries 3
```
2. Validar y reiniciar:
```bash
sudo sshd -t
sudo systemctl restart ssh
sudo journalctl -u ssh -n 50 --no-pager
```

### Criterio de exito
- Login root bloqueado.
- Login por password bloqueado.
- Solo acceso por llave publica.

---

## Lab 3: Verificacion de DNSSEC y correo seguro
### Objetivo
Validar autenticidad DNS y postura minima de email.

### Pasos
```bash
dig +dnssec ejemplo.com A
dig +short TXT ejemplo.com
dig +short TXT selector._domainkey.ejemplo.com
dig +short TXT _dmarc.ejemplo.com
```

### Criterio de exito
- DNSSEC con firmas cuando aplique.
- SPF/DKIM/DMARC presentes y coherentes.

---

## Lab 4: Baseline de logging y deteccion
### Objetivo
Crear detecciones basicas de alto valor.

### Pasos
1. Activar recoleccion de logs de auth y sistema.
2. Generar actividad de prueba:
```bash
for i in {1..5}; do ssh usuario@localhost; done
sudo useradd test_soc
```
3. Buscar eventos:
```bash
sudo journalctl --since '15 min ago' | rg -i 'failed|invalid|useradd|sudo'
```

### Criterio de exito
- Detectas intentos fallidos repetidos.
- Detectas creacion de usuario nuevo.

---

## Lab 5: Mini tabletop de incidente
### Escenario
Compromiso de cuenta admin por phishing.

### Tareas
1. Contener: bloquear cuenta y sesiones activas.
2. Analizar: revisar IP origen, cambios de privilegios y accesos.
3. Erradicar: rotar secretos/tokenes comprometidos.
4. Recuperar: restaurar acceso legitimo y monitoreo 48h.
5. Documentar: postmortem tecnico con acciones.

### Criterio de exito
- Tiempo de contencion menor a 30 minutos (simulado).
- Lecciones traducidas a cambios concretos de control.

## Nota legal y etica
Practica solo en entornos propios o autorizados.
