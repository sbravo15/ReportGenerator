# 02 - Protocolos Criticos (tecnico y directo)

## 1) TLS 1.3 / HTTPS
- Capa: aplicacion sobre TCP.
- Puerto tipico: 443.
- Objetivo: confidencialidad, integridad y autenticacion del servidor.

### Flujo tecnico resumido
1. ClientHello: cliente envia versiones/cifrados soportados.
2. ServerHello: servidor negocia parametros y envia certificado.
3. Intercambio de llaves efimeras (ECDHE) para secrecy hacia adelante.
4. Se establecen claves de sesion y arranca trafico cifrado.

### Hardening minimo
- Permitir TLS 1.2 y TLS 1.3 (idealmente priorizar 1.3).
- Deshabilitar TLS 1.0/1.1 y ciphers debiles.
- Certificados validos, no auto-firmados en produccion.
- HSTS y redireccion forzada a HTTPS.

### Validacion rapida
```bash
openssl s_client -connect ejemplo.com:443 -tls1_3
nmap --script ssl-enum-ciphers -p 443 ejemplo.com
curl -I https://ejemplo.com
```

## 2) SSH (Secure Shell)
- Capa: aplicacion sobre TCP.
- Puerto tipico: 22.
- Objetivo: acceso remoto seguro y tuneles cifrados.

### Hardening minimo
- `PasswordAuthentication no`
- `PermitRootLogin no`
- Solo llaves publicas y usuarios permitidos.
- Limitar intentos (`MaxAuthTries`) y usar fail2ban.

### Validacion rapida
```bash
sudo sshd -t
ss -tulpen | grep :22
sudo journalctl -u ssh -n 100 --no-pager
```

## 3) DNS y DNSSEC
- DNS: resolucion de nombres.
- DNSSEC: agrega firma criptografica para validar autenticidad de respuestas DNS.
- Puertos: 53 (UDP/TCP).

### Riesgo sin DNSSEC
- Cache poisoning y respuestas DNS falsificadas.

### Validacion rapida
```bash
dig +dnssec ejemplo.com A
dig +short TXT _dmarc.ejemplo.com
```

## 4) IPsec / IKEv2 (VPN)
- Capa: red.
- Puertos IKEv2: UDP 500 y 4500 + ESP.
- Objetivo: tunel cifrado entre hosts o redes.

### Hardening minimo
- IKEv2 con algoritmos modernos (AES-GCM, SHA-2).
- Certificados o llaves robustas.
- Rotacion de llaves y tiempos de vida razonables.
- Acceso minimo por segmento/ACL.

### Validacion rapida
```bash
sudo ip xfrm state
sudo ip xfrm policy
```

## 5) OAuth 2.0 + OpenID Connect (OIDC)
- Objetivo: autorizacion delegada (OAuth2) y autenticacion federada (OIDC).
- Uso tipico: login SSO y acceso de apps a APIs.

### Buenas practicas minimas
- Authorization Code Flow + PKCE.
- Tokens de corta vida y refresh token protegido.
- Validar `iss`, `aud`, `exp`, `nonce` (OIDC/JWT).
- Nunca usar Implicit Flow en implementaciones nuevas.

### Errores comunes
- Guardar tokens en lugares inseguros del browser.
- No validar firma o claims del token.
- Scope excesivo para clientes.

## 6) Seguridad de correo: SPF, DKIM, DMARC
- SPF: autoriza IPs/hosts que pueden enviar correo de tu dominio.
- DKIM: firma criptografica del mensaje.
- DMARC: politica de alineacion y reportes basada en SPF/DKIM.

### DNS records base
- SPF (TXT): `v=spf1 include:_spf.proveedor.com -all`
- DKIM (TXT selector): clave publica del dominio.
- DMARC (TXT): `v=DMARC1; p=quarantine; rua=mailto:...`

### Validacion rapida
```bash
dig +short TXT ejemplo.com
dig +short TXT selector._domainkey.ejemplo.com
dig +short TXT _dmarc.ejemplo.com
```

## Tabla de prioridad para beginner
1. TLS/HTTPS
2. SSH
3. SPF/DKIM/DMARC
4. OAuth2/OIDC
5. DNSSEC
6. IPsec/IKEv2

Razon: primero proteger acceso remoto, web y correo (superficie de ataque mas frecuente), luego identidad federada y red avanzada.
