201~200~# PROPUESTA FORMAL DE CONTINUIDAD

## Morpho Agents — Cierre de estabilización y decisión de despliegue

**Fecha:** 24 de julio de 2026
**Objetivo de despliegue vigente:** 1 de agosto de 2026
**Estado del alcance:** Congelado conforme a `DEPLOYMENT_CONTRACT.md`

---

# 1. CONTEXTO

Durante las últimas sesiones se investigaron los rechazos de Hyperliquid con el mensaje:

`Insufficient margin to place order`

La investigación recorrió:

* `execution_agent.py`
* `execution_workflow.py`
* `risk_manager.py`
* `portfolio_state.py`
* `account_visibility.py`
* Estado operativo y logs de Hyperliquid
* Restricciones del `DEPLOYMENT_CONTRACT.md`

La conclusión fue:

* No se encontró un defecto local concreto.
* No se encontró corrupción de posiciones ni del estado interno.
* Hyperliquid recibe la orden y la rechaza por falta de margen disponible.
* Morpho no dispone actualmente de una política de admisión basada en capacidad real de la cuenta.
* Implementar esa política introduciría una nueva responsabilidad arquitectónica.
* El cambio no está autorizado por el alcance de despliegue vigente.
* El descubrimiento quedó registrado en `FUTURE_IDEAS.md`.

La investigación fue técnicamente válida, pero consumió demasiadas sesiones para producir únicamente una conclusión documental.

---

# 2. PROBLEMA DE PROCESO IDENTIFICADO

El problema principal no fue la conclusión técnica.

El problema fue el coste del proceso.

La investigación continuó después de que ya existían suficientes indicios para determinar que:

1. El rechazo provenía del exchange.
2. No había evidencia de corrupción interna.
3. Resolverlo exigía una política nueva.
4. La política estaba fuera del alcance autorizado.

La búsqueda adicional aumentó la certeza, pero no cambió la decisión.

Por tanto, el proceso de estabilización debe incorporar un criterio explícito de cierre temprano.

---

# 3. DECISIÓN PROPUESTA

A partir de esta fecha, Morpho entra en una fase estricta de:

## DEPLOYMENT CLOSURE

El objetivo ya no será descubrir mejoras arquitectónicas.

El objetivo será determinar, con evidencia mínima suficiente, si Morpho puede desplegarse con capital real bajo riesgos explícitamente aceptados.

La prioridad será:

1. Verificar el estado real de los elementos autorizados.
2. Medir el impacto de los incidentes abiertos.
3. Corregir únicamente defectos bloqueantes y autorizados.
4. Preparar una decisión formal de despliegue.
5. Evitar cualquier ampliación automática del alcance.

---

# 4. TRATAMIENTO DEL INCIDENTE DE MARGEN

El rechazo `Insufficient margin` queda clasificado provisionalmente como:

## DESCUBRIMIENTO NO BLOQUEANTE PENDIENTE DE MEDICIÓN

No se implementará una política de admisión antes del despliegue, salvo cambio formal y escrito del contrato.

El incidente solo se elevará a bloqueante si aparece evidencia de uno o más de estos efectos:

* Corrupción o divergencia del estado interno.
* Posiciones registradas localmente que no existen en el exchange.
* Órdenes ejecutadas sin stop loss o take profit.
* Reintentos continuos que produzcan rate limiting relevante.
* Bloqueo prolongado de oportunidades ejecutables.
* Degradación material de la operativa.
* Riesgo directo para capital real.
* Fallos secundarios provocados por la respuesta del exchange.

En ausencia de esas consecuencias, el rechazo será considerado una respuesta válida del exchange ante una cuenta sin capacidad suficiente.

---

# 5. PLAN DE CONTINUIDAD

## SESIÓN 1 — DEPLOYMENT READINESS REVIEW

### Objetivo

Establecer el estado real y verificable de todos los elementos necesarios para la decisión del 1 de agosto.

### Trabajo

Revisar, sin modificar inicialmente:

* Estado del servicio.
* Estado del repositorio.
* Último commit desplegado.
* Seis elementos originales del contrato.
* ITEM 7 de visibilidad de cuenta.
* Kill switch.
* Posiciones abiertas.
* Órdenes abiertas.
* Balance y margen disponible.
* Últimas ejecuciones aprobadas y rechazadas.
* Estado de stop loss y take profit.
* Divergencias entre base de datos y exchange.
* Incidentes abiertos.

### Resultado obligatorio

Una tabla con:

* Elemento.
* Estado.
* Evidencia.
* Riesgo.
* Acción necesaria.
* Clasificación: bloqueante o no bloqueante.

No se modificará código durante esta revisión, salvo que aparezca un defecto crítico, reproducible y claramente perteneciente a uno de los elementos autorizados.

---

## SESIÓN 2 — TRIAGE DE INCIDENTES

### Objetivo

Clasificar cada incidente abierto por impacto real, no por interés técnico.

### Incidentes mínimos a revisar

* INC-001: alertas de Telegram.
* INC-002: tendencia `UNKNOWN`.
* INC-003: RSI placeholder.
* Rechazos por margen insuficiente.
* Cualquier divergencia entre exchange y base de datos.
* Cualquier posición sin protección.
* Cualquier fallo del kill switch.

### Clasificación obligatoria

Cada incidente deberá terminar en una de estas categorías:

### A. BLOQUEANTE

Impide el despliegue o pone directamente en riesgo el capital.

### B. RIESGO ACEPTABLE

Puede desplegarse con el riesgo expresamente documentado.

### C. FUERA DE ALCANCE

Se registra para después del despliegue.

### D. RESUELTO

Existe evidencia de que ya no afecta al sistema.

No se abrirán investigaciones arquitectónicas sin una consecuencia operativa demostrable.

---

## SESIÓN 3 — DECISIÓN GO / NO-GO

### Objetivo

Tomar una decisión consciente antes o durante el 1 de agosto de 2026.

### Opción A — GO

Desplegar con capital real limitado.

Condiciones mínimas:

* Kill switch validado.
* Posiciones internas coherentes con el exchange.
* Stop loss operativo.
* No existen defectos bloqueantes conocidos.
* Riesgos restantes documentados.
* Capital inicial y exposición máxima definidos.
* Supervisión humana activa.
* Procedimiento de detención preparado.

### Opción B — LIMITED GO

Despliegue progresivo con capital mínimo y restricciones reforzadas.

Condiciones posibles:

* Una sola posición simultánea.
* Tamaño de posición reducido.
* Revisión manual diaria.
* Comprobación manual de balance y órdenes.
* Detención inmediata ante divergencia.
* Sin expansión de capital hasta acumular evidencia estable.

### Opción C — NO-GO

Posponer el despliegue.

Solo será válido si existe:

* Un defecto bloqueante concreto.
* Evidencia reproducible.
* Propietario claramente identificado.
* Alcance de reparación definido.
* Nueva fecha escrita.
* Criterio objetivo de cierre.

La incomodidad general o la existencia de mejoras futuras no serán motivos suficientes para posponer.

---

# 6. NUEVO PROTOCOLO DE INVESTIGACIÓN

Toda investigación durante la fase de cierre deberá seguir este orden:

## PASO 1 — COMPORTAMIENTO

Definir un único comportamiento observable.

## PASO 2 — IMPACTO

Determinar qué daño real produce.

## PASO 3 — PROPIETARIO

Identificar el único módulo responsable.

## PASO 4 — AUTORIZACIÓN

Comprobar si modificar ese propietario está permitido.

## PASO 5 — EVIDENCIA MÍNIMA

Recoger únicamente la evidencia necesaria para confirmar o rechazar la hipótesis.

## PASO 6 — DECISIÓN

Terminar en una de estas salidas:

* Corregir.
* Aceptar el riesgo.
* Documentar para el futuro.
* Descartar la hipótesis.

## PASO 7 — CIERRE

No continuar inspeccionando módulos si la decisión ya no puede cambiar.

---

# 7. REGLA DE LÍMITE DE INVESTIGACIÓN

Una investigación se detendrá cuando se cumplan estas tres condiciones:

1. El origen del comportamiento esté suficientemente identificado.
2. El impacto operativo esté entendido.
3. La decisión de modificar o no modificar ya esté determinada por el contrato.

La certeza absoluta no será necesaria cuando evidencia adicional no pueda cambiar la decisión.

---

# 8. REGLA DE CAMBIO DE CÓDIGO

Antes de cualquier modificación deberá existir una declaración explícita:

## SCOPE CHECK

**Comportamiento:**
[Un único comportamiento]

**Propietario:**
[Un único archivo o módulo]

**Evidencia:**
[Prueba concreta]

**Elemento autorizado:**
[Número del Deployment Contract]

**Cambio previsto:**
[Modificación concreta]

**Validación:**
[Prueba que confirmará o rechazará la hipótesis]

Si no puede completarse esta declaración, no se modificará código.

---

# 9. PRIORIDAD OPERATIVA

Hasta la decisión de despliegue, el orden de prioridad será:

1. Riesgo directo para capital.
2. Kill switch.
3. Coherencia entre exchange y estado interno.
4. Protección de posiciones.
5. Ejecución correcta.
6. Observabilidad necesaria para supervisión.
7. Calidad de señales.
8. Mejoras arquitectónicas futuras.

Ninguna mejora de arquitectura tendrá prioridad sobre una validación operativa pendiente.

---

# 10. RESULTADO ESPERADO

Esta propuesta busca asegurar que las próximas sesiones produzcan uno de estos resultados concretos:

* Un defecto bloqueante corregido.
* Un riesgo explícitamente aceptado.
* Un elemento contractual validado.
* Una decisión formal de despliegue.
* Una razón objetiva y documentada para posponer.

No se considerará progreso suficiente acumular inspecciones sin una decisión operativa.

---

# 11. PRÓXIMO PASO RECOMENDADO

La próxima sesión debe comenzar como:

## DEPLOYMENT READINESS REVIEW

No debe comenzar investigando nuevamente el rechazo por margen.

El rechazo por margen solo se revisará para medir frecuencia e impacto, no para diseñar una solución.

El entregable de esa sesión será una matriz completa de preparación para despliegue y una lista limitada de bloqueantes reales.

---

# DECISIÓN PROPUESTA

Adoptar este plan como protocolo de cierre hasta el 1 de agosto de 2026.

Mantener congelado el alcance actual.

No implementar la política de admisión de margen antes del despliegue.

Priorizar evidencia operativa, cierre de elementos autorizados y decisión formal GO / LIMITED GO / NO-GO.

La siguiente sesión deberá producir una evaluación integral de preparación para despliegue, no una nueva investigación abierta.
