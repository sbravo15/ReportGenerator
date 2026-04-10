# 01 - Skills Primordiales

## Skill Matrix (prioridad alta a baja)

### 1) Networking defensivo
- Debes dominar: modelo TCP/IP, puertos, estados de conexion, subneteo basico, ACL/firewall.
- Por que importa: sin red no puedes detectar ni contener incidentes.
- Minimo tecnico:
  - Explicar handshake TCP y handshake TLS.
  - Interpretar `ss -tulpen`, `netstat`, `tcpdump`, `wireshark`.
  - Distinguir trafico normal vs anomalo basico (escaneos, conexiones repetidas, puertos no esperados).

### 2) Linux y hardening base
- Debes dominar: usuarios/grupos, permisos, `sudo`, servicios, logs (`journalctl`, `/var/log/*`).
- Por que importa: la mayoria de cargas criticas corren en Linux o derivados.
- Minimo tecnico:
  - Deshabilitar login SSH por password y por root.
  - Aplicar actualizaciones de seguridad.
  - Habilitar firewall host (`ufw`/`nftables`) y fail2ban.

### 3) IAM (Identity and Access Management)
- Debes dominar: principio de menor privilegio, MFA, ciclo de vida de cuentas.
- Por que importa: la identidad es el nuevo perimetro.
- Minimo tecnico:
  - Diseñar 3 roles (admin, operador, lectura) con permisos claros.
  - Implementar MFA para cuentas privilegiadas.
  - Eliminar cuentas huerfanas y credenciales compartidas.

### 4) Criptografia aplicada
- Debes dominar: cifrado en transito, hashing, firmas, PKI, certificados.
- Por que importa: evita robo/manipulacion de datos y suplantacion.
- Minimo tecnico:
  - Diferenciar AES vs RSA/ECC vs SHA-2/3.
  - Entender cadena de confianza X.509.
  - Detectar configuraciones debiles (TLS viejo, cipher inseguros, cert expirado).

### 5) Seguridad de aplicaciones (AppSec basico)
- Debes dominar: OWASP Top 10, validacion de entradas, auth segura, manejo de secretos.
- Por que importa: muchas brechas entran por aplicaciones web/API.
- Minimo tecnico:
  - Identificar riesgo de Injection, Broken Access Control y Cryptographic Failures.
  - Revisar headers de seguridad HTTP.
  - Separar secretos de codigo fuente.

### 6) Logging, monitoreo y deteccion
- Debes dominar: fuentes de log, normalizacion, alertas por casos de uso.
- Por que importa: no se puede responder lo que no se ve.
- Minimo tecnico:
  - Activar logs de autenticacion, red y aplicacion.
  - Crear 3 alertas: login fallido masivo, nueva cuenta admin, proceso sospechoso.
  - Definir retencion minima y timestamps sincronizados (NTP).

### 7) Vulnerability management
- Debes dominar: inventario de activos, escaneo, priorizacion por riesgo, parcheo.
- Por que importa: reduce superficie explotable.
- Minimo tecnico:
  - Mantener inventario de software/servicios.
  - Priorizar CVEs por criticidad + exposicion + exploitabilidad.
  - Medir tiempo de remediacion (MTTR de vulnerabilidades).

### 8) Respuesta a incidentes
- Debes dominar: preparacion, deteccion, contencion, erradicacion, recuperacion, lecciones.
- Por que importa: la pregunta no es si pasa, sino cuando.
- Minimo tecnico:
  - Ejecutar tabletop de ransomware o compromiso de cuenta.
  - Preservar evidencia (logs, hashes, timeline).
  - Publicar postmortem sin culpables y con acciones.

## Meta de competencia (Beginner tecnico)
Debes poder explicar, configurar y validar controles basicos sin copiar pasos a ciegas. Si no puedes justificar un control, aun no esta dominado.
