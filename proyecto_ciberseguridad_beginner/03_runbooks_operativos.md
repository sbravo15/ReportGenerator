# 03 - Runbooks Operativos

## Runbook A: Respuesta a incidentes (IR)
Basado en ciclo: preparar -> detectar -> analizar -> contener -> erradicar -> recuperar -> lecciones.

### A1. Preparacion
1. Definir equipo IR (tecnico, legal, negocio, comunicacion).
2. Inventario de activos criticos y dueños.
3. Fuentes de log habilitadas (auth, endpoint, red, app).
4. Canales de escalamiento y guardias.

### A2. Deteccion y analisis
1. Recibir alerta (SIEM/EDR/usuario).
2. Clasificar severidad:
   - Sev1: impacto critico o activo comprometido sensible.
   - Sev2: impacto parcial, contencion posible.
   - Sev3: evento sospechoso sin impacto confirmado.
3. Correlacionar evidencia:
   - IOC: IP, hash, dominio, usuario, proceso.
   - Timeline con hora UTC.
4. Abrir ticket de incidente con ID unico.

### A3. Contencion
1. Corto plazo: aislar host/usuario/token.
2. Largo plazo: reglas permanentes (firewall, EDR policy, IAM).
3. Preservar evidencia antes de limpiar.

### A4. Erradicacion y recuperacion
1. Eliminar malware/persistencia.
2. Rotar credenciales y llaves expuestas.
3. Parchar causa raiz.
4. Restaurar servicio y monitorear rebrote 24-72h.

### A5. Lecciones aprendidas
1. Postmortem en menos de 5 dias habiles.
2. Definir acciones con owner y fecha.
3. Actualizar playbooks, detecciones y hardening.

---

## Runbook B: Gestion de vulnerabilidades

### B1. Ciclo minimo
1. Descubrimiento: inventario y escaneo programado.
2. Priorizacion: CVSS + explotabilidad + exposicion + valor del activo.
3. Remediacion: parche, mitigacion temporal o compensatorio.
4. Verificacion: re-escaneo y cierre con evidencia.

### B2. SLA sugerido
- Critico expuesto a internet: 48-72 horas.
- Alto: 7-15 dias.
- Medio: 30 dias.
- Bajo: 60-90 dias.

### B3. KPIs minimos
- % de activos inventariados.
- Tiempo medio de remediacion (MTTR-vuln).
- % de vulnerabilidades criticas fuera de SLA.

---

## Runbook C: Control de cambios de seguridad
1. Todo cambio de seguridad debe tener:
   - Justificacion de riesgo.
   - Plan de rollback.
   - Ventana de mantenimiento.
   - Evidencia de prueba previa.
2. Ningun cambio critico sin aprobacion dual.
3. Post cambio: validacion tecnica y monitoreo reforzado.
