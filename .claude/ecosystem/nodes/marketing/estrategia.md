# Estrategia de Lanzamiento: ChandeliERP
## Para Founder Solo · Presupuesto $0 · Pre-Revenue

> **Versión:** 2.0 — Febrero 2026
> **Objetivo:** Generar los primeros 1-3 clientes de pago en 90 días.

---

## 1. Diagnóstico Crítico de la Estrategia Anterior

La estrategia v1.0 fue un ejercicio aspiracional desconectado de la realidad. Este diagnóstico documenta las desconexiones para evitar repetirlas.

### 1.1 Reality Check: Lo Prometido vs Lo Real

| Lo que asumía la estrategia v1.0 | La realidad (Feb 2026) |
|---|---|
| Equipo de marketing + ventas dedicado | 1 founder solo (dev + ventas + soporte) |
| Presupuesto para ads, webinars, talleres presenciales | $0 COP disponible para marketing |
| Producto con facturación DIAN integrada | No existe — se usan facturas PDF |
| Integración Shopify/WooCommerce | No existe ni hay demanda validada |
| Multi-bodega | No implementado |
| API abierta para terceros | No existe |
| 500 usuarios en Q1-Q2 | 1 beta tester activo |
| Landing page con funnel de conversión | No existe landing page |
| Sistema de pagos integrado (gateway) | Cero gateways — cobro manual |
| PLG con signup self-service | SuperAdmin crea tenants manualmente |
| Soporte 24/7 | No existe módulo de soporte |
| Programa de referidos automatizado | No existe |

### 1.2 Errores Fundamentales

1. **Pricing basado en features inexistentes:** 4 planes (Spark $0 → Ignite $249.900) donde el 60% de las features diferenciadores no existen (DIAN, Shopify, multi-bodega, API).
2. **Canales que requieren dinero o equipo:** Webinars, talleres presenciales, retargeting, alianzas con proveedores — imposibles para 1 persona con $0.
3. **Métricas fantasía:** 500 usuarios en 6 meses sin ningún canal de adquisición funcional.
4. **Posicionamiento genérico:** "ERP vertical para cerería" compite con Alegra/Siigo en terreno donde ellos tienen marca y presupuesto.

### 1.3 Qué SÍ Tiene Valor de la v1.0

- La identificación del dolor principal es correcta: los cereros no saben cuánto les cuesta cada vela.
- El "momento aha" (ver el costo unitario exacto) sigue siendo la palanca de activación.
- El mercado de cerería artesanal en Cali es real y desatendido por software.

---

## 2. Posicionamiento y Propuesta de Valor

### 2.1 Mensaje Central

> **"ChandeliERP es el sistema que te dice exactamente cuánto te cuesta cada vela — y cuánto deberías cobrar."**

No es un "ERP completo". No es "facturación DIAN". Es **la calculadora de rentabilidad que todo cerero necesita y nadie tiene**.

### 2.2 Diferenciación Real (Features Verificadas en el Codebase)

Cada feature listada aquí **existe y funciona** en la versión actual:

| Feature | Qué resuelve | Archivos clave |
|---|---|---|
| **BOM/Recetas con costeo unitario** | "¿Cuánto me cuesta esta vela incluyendo merma y mano de obra?" | `backend/app/rutas/recetas.py`, `frontend/src/pages/RecetasPage.tsx` |
| **Inventario con costo promedio ponderado** | "¿A cuánto tengo valorizado mi stock real?" | `backend/app/datos/modelos.py` (campo `costo_promedio`) |
| **POS integrado** | "Vendo y el inventario se descuenta automáticamente" | `frontend/src/pages/POSPage.tsx`, `frontend/src/stores/posStore.ts` |
| **Dashboard en tiempo real (SSE)** | "Veo mis ventas del día sin recargar la página" | `backend/app/rutas/sse.py`, `frontend/src/hooks/useSSE.ts` |
| **CRM con pipeline Kanban** | "Sigo mis prospectos desde el primer contacto hasta el cierre" | `frontend/src/pages/CRMPage.tsx`, `frontend/src/components/crm/KanbanBoard.tsx` |
| **Cartera con aging** | "Sé quién me debe, cuánto y hace cuánto" | `backend/app/rutas/cartera.py`, `frontend/src/pages/CarteraPage.tsx` |

### 2.3 Posicionamiento Competitivo

| Competidor | Precio | BOM/Recetas | POS | CRM | Localización CO |
|---|---|---|---|---|---|
| Alegra | ~$80.000/mes | ❌ | ❌ | ❌ | ✅ (DIAN) |
| Siigo | ~$100.000/mes | ❌ | ✅ | ❌ | ✅ (DIAN) |
| Katana MRP | ~$350.000/mes | ✅ | ❌ | ❌ | ❌ |
| Craftybase | ~$120.000/mes | ✅ | ❌ | ❌ | ❌ |
| **ChandeliERP** | **Desde $5.000/mes** | **✅** | **✅** | **✅** | **Parcial** |

**Ventaja:** Nadie ofrece BOM + POS + CRM integrados a precio accesible para micro-cereros colombianos.

**Desventaja honesta:** No tenemos facturación DIAN. Para los primeros clientes esto no es bloqueante (usan facturas en PDF o no facturan electrónicamente), pero limita el mercado a negocios pequeños/informales.

### 2.4 Perfil del Cliente Ideal (ICP)

**Persona: "La Cerera de Cali"**

- **Quién:** Mujer emprendedora, 25-45 años, produce velas artesanales (aromáticas, decorativas, religiosas)
- **Dónde:** Cali y Valle del Cauca (mercado inicial — expansión orgánica después)
- **Tamaño:** 1-5 empleados, factura $2M-$20M COP/mes
- **Dolor principal:** No sabe si gana o pierde dinero por vela. Costea "a ojo" o en un cuaderno.
- **Tecnología:** Usa WhatsApp, Instagram, tal vez Excel. No ha usado un ERP nunca.
- **Motivación:** Quiere profesionalizar su negocio para crecer, pero no puede pagar Alegra/Siigo ni tiene tiempo para aprender software complejo.
- **Canal de comunicación preferido:** WhatsApp (no email)

### 2.5 Anti-Personas (A Quién NO Venderle)

| Anti-persona | Por qué no |
|---|---|
| Fábricas grandes (+20 empleados) | Necesitan DIAN, multi-bodega, ERP completo. No somos eso (aún). |
| Cereros que solo venden por Shopify/Mercado Libre | Necesitan integración e-commerce que no tenemos. |
| Personas que "solo quieren cotizar" | No van a usar el sistema completo. Pérdida de tiempo en onboarding. |
| Negocios que requieren facturación electrónica DIAN obligatoria | No tenemos esta feature. Ser honestos desde el día 1. |

---

## 3. Pricing: Pay-What-You-Want (PWYW)

### 3.1 El Modelo

| Elemento | Detalle |
|---|---|
| **Trial gratuito** | 14 días con onboarding asistido por el founder |
| **Después del trial** | El usuario elige cuánto pagar cada mes |
| **Precio mínimo** | $5.000 COP/mes (~$1.25 USD) |
| **Precio máximo** | Sin límite |
| **Features bloqueadas** | Ninguna — acceso completo siempre |
| **Método de cobro** | Transferencia Nequi o Bancolombia (sin gateway) |
| **Cadencia** | Mensual — el founder pregunta cada mes |

### 3.2 Por Qué PWYW y No Planes Fijos

**Para el usuario:**
- Barrera de entrada mínima: "¿$5.000? ¿Qué puedo perder?"
- Control total: el usuario siente que decide, no que le venden
- Sin "upgrade walls" frustrantes — todo funciona desde el día 1

**Para el founder:**
- Cada peso recibido es señal directa de valor percibido
- Feedback implícito: si alguien paga $5.000 tras un mes de uso intensivo, algo no le sirvió
- Si paga $50.000, hay product-market fit en esa persona
- No hay que invertir tiempo diseñando/manteniendo planes y restricciones

**Evidencia de que funciona:**
- Humble Bundle: precio promedio 3-5x sobre el mínimo
- Radiohead (In Rainbows): generó más ingresos que álbumes anteriores con precio fijo
- Panera Bread (Panera Cares): funcionó 5 años en comunidades de confianza
- El modelo funciona mejor en comunidades pequeñas y de alta confianza — exactamente el caso de cereros artesanales en Cali

### 3.3 Psicología del PWYW en Contexto Colombiano

- La cultura colombiana valora la reciprocidad y la relación personal
- Si el founder hace onboarding 1-a-1 y el usuario ve valor, hay presión social positiva para pagar "justo"
- El WhatsApp como canal de cobro agrega un toque personal que los gateways eliminan
- "¿Cuánto vale esto para ti este mes?" es más poderoso que "Tu factura de $39.900 está lista"

### 3.4 Métricas Clave del PWYW

| Métrica | Cómo medirla | Target (mes 3) |
|---|---|---|
| **Precio promedio pagado** | Suma total recibida / # usuarios activos | > $20.000 COP/mes |
| **Distribución de pagos** | Histograma de cuánto paga cada usuario | < 50% en el mínimo |
| **Tendencia mensual por usuario** | ¿El mismo usuario sube o baja lo que paga? | Tendencia estable o creciente |
| **Tasa de pago** | % de usuarios post-trial que pagan (cualquier monto) | > 60% |

### 3.5 Cuándo Migrar a Planes Fijos

El PWYW es un vehículo de descubrimiento de precio, no el modelo permanente. Migrar cuando:

1. **Hay 15+ usuarios pagando** — suficiente muestra para estadísticas
2. **El precio promedio se estabiliza** durante 2+ meses — el mercado encontró su precio
3. **Se identifican 2-3 clusters naturales** en la distribución (ej: grupo de $10.000, grupo de $30.000, grupo de $60.000)
4. **Los clusters se correlacionan con uso:** los que pagan más usan features específicas → base para tiers

**Cómo migrar:**
- Usar el precio promedio como referencia para el plan "estándar"
- Los early adopters PWYW mantienen su modelo como beneficio de founder
- Los nuevos usuarios entran con planes fijos basados en los clusters descubiertos

---

## 4. Estrategia de Adquisición (4 Canales, $0)

Canales ordenados por velocidad de impacto. Todos son orgánicos y ejecutables por 1 persona.

### Canal 1: Outreach Directo (WhatsApp + Instagram DMs) — Impacto Inmediato

**Estrategia:** Mensajes personalizados 1-a-1 a cereros identificados en Cali.

**Dónde encontrar prospectos:**
- **Instagram:** Buscar hashtags `#velascali` `#ceroscali` `#velasartesanales` `#velascolombia` `#cirios` `#velasdecorativas`
- **Google Maps:** Buscar "velas artesanales cali", "cirios cali", "velas decorativas cali"
- **Cámara de Comercio Cali:** Directorio de negocios registrados en manufactura
- **Grupos de Facebook:** "Emprendedores Cali", "Artesanos del Valle", "Velas y Cirios Colombia"
- **Mercado Libre / Linio:** Vendedores de velas en Cali (ver perfil → contacto)

**Volumen:** 5 mensajes personalizados por día (25 por semana)

**Conversión esperada:**
- Respuesta: 10-15% (2-3 de cada 25)
- Trial: 3-5% del total (1 de cada 25)
- Es decir: ~1 trial nuevo por semana

**Script de primer contacto (WhatsApp):**

> Hola [Nombre] 👋 Vi tu trabajo en [Instagram/Google Maps] — ¡qué lindas las velas de [tipo específico]!
>
> Te escribo porque estoy desarrollando un software específico para cereros que calcula automáticamente cuánto te cuesta cada vela (incluyendo la merma, la mano de obra, todo).
>
> Tengo una versión que puedes probar gratis 14 días. Si te interesa, te hago una demo de 30 min por videollamada y te ayudo a cargar tus primeros productos.
>
> ¿Te gustaría verlo?

**Script de seguimiento (si no responde, día 3):**

> Hola [Nombre], solo te dejo este video cortito donde muestro cómo funciona 👇 [link al video demo]
>
> Si en algún momento te interesa, me avisas. ¡Éxitos con tu negocio!

**Reglas del outreach:**
- SIEMPRE personalizar (mencionar algo específico de su negocio)
- NUNCA copiar-pegar masivo — se nota y genera rechazo
- NUNCA insistir más de 2 veces — si no responde al seguimiento, pasar al siguiente
- Llevar un registro simple (Google Sheets) de: nombre, negocio, fecha contacto, respuesta, estado

### Canal 2: SEO + Blog — Impacto a 3-6 Meses

**Estrategia:** 1 artículo semanal de 800-1.200 palabras alojado en la landing page (sección blog).

**Por qué funciona:** La competencia SEO en español para cerería es prácticamente **CERO**. Con contenido básico pero bien estructurado, se puede ser #1 en Google para estas búsquedas en 2-3 meses.

**Keywords Objetivo (baja competencia, alta intención):**

| Keyword | Intención | Volumen estimado | Dificultad |
|---|---|---|---|
| "cómo calcular el costo de una vela" | Informacional → transaccional | Bajo pero ultra-relevante | Muy baja |
| "software para cerería" | Transaccional directa | Muy bajo | Casi nula |
| "control de inventario velas artesanales" | Transaccional | Bajo | Baja |
| "cuánto cobrar por una vela" | Informacional → transaccional | Medio | Baja |
| "cómo saber si mi negocio de velas es rentable" | Informacional | Medio | Baja |
| "recetas de velas con costos" | Informacional | Medio | Baja |
| "merma en producción de velas" | Informacional | Bajo | Casi nula |
| "cera de soya vs parafina costos" | Informacional | Medio | Baja |

**Estructura de cada artículo:**
1. Título con keyword principal
2. Introducción (problema que resuelve)
3. Contenido educativo real (que el cerero aprenda algo útil)
4. Ejemplo con números reales
5. CTA suave: "Si quieres automatizar este cálculo, prueba ChandeliERP gratis 14 días → [link]"

**Calendario editorial (primeras 8 semanas):**

| Semana | Artículo | Keyword principal |
|---|---|---|
| 3 | "Guía completa: Cómo calcular el costo real de una vela artesanal" | cómo calcular el costo de una vela |
| 4 | "¿Estás cobrando lo suficiente? Cómo fijar precios en cerería" | cuánto cobrar por una vela |
| 5 | "Control de inventario para cereros: Del cuaderno al sistema" | control de inventario velas artesanales |
| 6 | "La merma invisible: Cuánto dinero pierdes sin saberlo" | merma en producción de velas |
| 7 | "Cera de soya vs parafina: Comparativa de costos reales" | cera de soya vs parafina costos |
| 8 | "5 señales de que tu negocio de velas no es rentable (y cómo arreglarlo)" | negocio de velas es rentable |
| 9 | "Cómo organizar las recetas de tus velas para escalar producción" | recetas de velas con costos |
| 10 | "El software que los cereros no sabían que necesitaban" | software para cerería |

**Herramientas gratuitas:**
- Google Search Console (indexación y métricas de búsqueda)
- Google Analytics 4 (tráfico y comportamiento)
- Ubersuggest versión gratuita (investigación de keywords)
- AnswerThePublic versión gratuita (ideas de contenido)

### Canal 3: Video Demo — Asset de Conversión Permanente

**Estrategia:** 1 video de 5 minutos mostrando el flujo completo de valor.

**Guión del video:**

| Minuto | Contenido |
|---|---|
| 0:00-0:30 | Hook: "¿Sabes exactamente cuánto te cuesta cada vela que produces? La mayoría de cereros no. Hoy te muestro cómo saberlo en segundos." |
| 0:30-1:30 | Crear una receta: agregar ingredientes (cera, fragancia, pabilo, colorante), definir cantidades, merma, mano de obra |
| 1:30-2:30 | El momento mágico: el sistema calcula el costo unitario exacto. "Esta vela de soya te cuesta $4.200 — ¿la estás vendiendo a $12.000? Tu margen es 65%." |
| 2:30-3:30 | Registrar una venta en el POS → el inventario se actualiza automáticamente → el dashboard muestra la venta en tiempo real |
| 3:30-4:30 | Vista de cartera: quién te debe, cuánto, hace cuánto. CRM: seguimiento de clientes potenciales. |
| 4:30-5:00 | CTA: "Prueba gratis 14 días. Yo te ayudo a configurar todo en una videollamada de 30 minutos. Link en la descripción." |

**Dónde publicarlo:**
- Landing page (hero section o sección dedicada)
- YouTube (con título SEO-optimizado)
- Instagram Reels (versión corta de 60 segundos con lo más impactante)
- WhatsApp (enviar directamente a prospectos en outreach)

**Herramientas gratuitas:**
- Loom (gratis hasta 25 videos de 5 min)
- OBS Studio (grabación de pantalla sin límite, gratis)
- CapCut (edición de video gratis, exportación sin marca de agua)

**Este video es el activo de ventas más importante.** Reemplaza 10 llamadas de venta. Un prospecto que ve el video y dice "quiero probarlo" ya está 80% convencido.

### Canal 4: Instagram Orgánico — Visibilidad de Marca

**Estrategia:** 3 posts por semana (Reels cortos de 30-60 segundos).

**Tipos de contenido:**

| Tipo | Ejemplo | Frecuencia |
|---|---|---|
| **"¿Sabías que...?"** | "¿Sabías que la merma de fragancia puede ser hasta 15%? Eso significa que de cada $100.000 en fragancia, $15.000 se evaporan. Literalmente." | 1/semana |
| **Antes/Después** | Pantalla dividida: cuaderno con números borrosos vs dashboard de ChandeliERP con datos en tiempo real | 1/semana |
| **Tips de cerería** | "3 formas de reducir la merma de cera de soya" (contenido útil con sutil product placement) | 1/semana |

**Hashtags base:** `#velasartesanales` `#cereria` `#emprendimiento` `#cali` `#negociopropio` `#velascolombia` `#handmadecandles` `#emprendedorescali` `#pyme`

**Reglas:**
- NO posts de "nueva feature" o "actualización del sistema" — a nadie le importa
- SÍ posts que eduquen sobre cerería con el producto como herramienta natural
- La cuenta es sobre CERERÍA, no sobre software
- Responder TODOS los comentarios y DMs en menos de 24 horas

---

## 5. Estrategia de Activación

### 5.1 Flujo de Onboarding Asistido

El onboarding NO es self-service. El founder hace cada onboarding 1-a-1.

**Flujo:**

```
1. Prospecto acepta trial
   ↓
2. Agendar videollamada de 30 min (Google Meet, gratis)
   ↓
3. Durante la llamada:
   a. Crear la cuenta del usuario
   b. Cargar sus primeros 5-10 productos/insumos
   c. Crear su primera receta con costos reales
   d. MOMENTO AHA: "Mira, esta vela te cuesta $4.200. ¿A cuánto la vendes?"
   e. Hacer una venta de prueba en el POS
   f. Mostrar el dashboard actualizándose en tiempo real
   ↓
4. Enviar por WhatsApp:
   - Link de acceso al sistema
   - PDF con "primeros pasos" (3 cosas para hacer esta semana)
   - "Cualquier duda me escribes por aquí"
```

### 5.2 Checklist de "Primer Éxito" del Usuario

El usuario se considera "activado" cuando completa al menos 3 de estos 5 hitos en los primeros 7 días:

- [ ] Tiene 5+ productos/insumos cargados con costos reales
- [ ] Ha creado 1+ receta con cálculo de costo unitario
- [ ] Ha registrado 1+ venta en el POS
- [ ] Ha revisado el dashboard al menos 2 veces
- [ ] Ha agregado 1+ cliente en el CRM

### 5.3 Métricas de Activación

| Métrica | Definición | Target |
|---|---|---|
| **Tasa de activación** | % de trials que completan 3+ hitos en 7 días | > 70% |
| **Tiempo a primer "aha"** | Minutos desde registro hasta ver costo unitario | < 45 min (durante onboarding) |
| **Retención día 7** | % de trials que ingresan al sistema en el día 7 | > 60% |

---

## 6. Estrategia de Conversión (Trial → PWYW)

### 6.1 Cadencia de Seguimiento por WhatsApp

| Día | Mensaje | Objetivo |
|---|---|---|
| **3** | "Hola [nombre], ¿cómo te ha ido con el sistema? ¿Has podido cargar tus otros productos?" | Resolver dudas tempranas, evitar abandono |
| **7** | "¿Ya viste cuánto te cuesta tu vela más vendida? Si necesitas ayuda con alguna receta, me avisas 🙂" | Reforzar el valor central |
| **10** | Compartir un tip útil: "Un truco: usa el CRM para anotar los pedidos de tus clientes frecuentes. Así no se te olvida ninguno." | Expandir el uso a más features |
| **12** | "Tu prueba termina en 2 días. ¿Qué te ha parecido? ¿Ha sido útil para tu negocio?" | Preparar la conversación de pago |
| **14** | "[Ver sección 6.2 — Conversación de conversión]" | Convertir |

### 6.2 La Conversación de Conversión

> Hola [nombre], tu período de prueba terminó hoy.
>
> Te cuento cómo funciona: ChandeliERP es "paga lo que quieras". Tú decides cuánto vale el servicio para ti cada mes. El mínimo es $5.000 COP (menos que un café).
>
> No hay funciones bloqueadas — todo lo que usaste estas 2 semanas sigue igual.
>
> ¿Cuánto quieres pagar este primer mes?

**Si dice que no quiere pagar:**
> Entiendo perfectamente. ¿Me puedes contar qué no te sirvió o qué esperabas que fuera diferente? Tu feedback me ayuda a mejorar.

(Este feedback vale más que $5.000 — documentarlo todo.)

**Si dice sí:**
> ¡Genial! Me puedes transferir a [Nequi/Bancolombia]: [número/cuenta]. Cuando quieras, sin afán.
>
> El mes que viene te vuelvo a preguntar — si el sistema te sirvió más, puedes subir el monto. Si te sirvió menos, puedes bajarlo. Tú decides siempre.

### 6.3 Manejo de Objeciones

| Objeción | Respuesta |
|---|---|
| "Muy caro" | "El mínimo es $5.000 — menos que un almuerzo. Y tú eliges si vale eso o no cada mes." |
| "No tengo tiempo de usarlo" | "¿Qué parte te quita más tiempo? Puedo ayudarte a automatizarla en 15 min por videollamada." |
| "Lo voy a pensar" | "Dale, sin presión. Te dejo el acceso abierto 3 días más para que lo pienses bien." |
| "No necesito software, mi cuaderno funciona" | "¿Sabes exactamente cuánto te cuesta cada vela? ¿Y cuál es tu margen real? El cuaderno no te dice eso automáticamente." |
| "No tiene facturación DIAN" | "Tienes razón, aún no. Si facturas electrónicamente hoy, este sistema no reemplaza eso todavía. Lo que sí hace es el costeo y control que Alegra/Siigo no hacen." |
| "Prefiero Excel" | "Excel funciona — pero no te calcula el costo cuando cambia el precio de la cera. Ni te descuenta el inventario cuando vendes. Ni te dice quién te debe." |

### 6.4 Método de Cobro

**Fase 1 (meses 1-6): Manual**
- Nequi: transferencia directa al número del founder
- Bancolombia: transferencia a cuenta de ahorros
- El founder envía comprobante por WhatsApp
- Registro en Google Sheets: fecha, usuario, monto, método

**Fase 2 (cuando haya 10+ usuarios): Semi-automatizado**
- Evaluar Wompi o Bold como gateway simple
- O automatizar recordatorio mensual por WhatsApp con link de Nequi

---

## 7. Estrategia de Retención

### 7.1 Check-ins (Primeros 30 Días Post-Pago)

| Semana | Acción |
|---|---|
| **1** | "¿Cómo te fue esta semana? ¿Registraste ventas en el POS?" |
| **2** | "Tip: revisa tu cartera — ¿hay alguien que te debe de hace más de 30 días?" |
| **3** | "¿Has probado el CRM? Si tienes clientes frecuentes, te ayuda a no perder pedidos." |
| **4** | "¡Un mes usando ChandeliERP! ¿Cómo te sientes? ¿Hay algo que mejorarías?" |

Después del primer mes: check-in quincenal, luego mensual (en la conversación de cobro PWYW).

### 7.2 Módulo PQRS como Canal de Retención

El módulo de Soporte/PQRS (prerrequisito técnico, ver Sección 10) es una herramienta de retención:

- **El usuario se siente escuchado:** Puede reportar problemas y ver que se resuelven
- **Feedback directo:** Cada ticket es una mejora potencial del producto
- **Transparencia:** El usuario ve el estado de su solicitud (ABIERTO → EN_PROCESO → RESUELTO)
- **Reducción de churn:** Un usuario frustrado que puede crear un ticket es menos probable que abandone silenciosamente

### 7.3 Feature Requests como Retención

Cuando un usuario pide una feature:
1. Crear un ticket PQRS tipo "Sugerencia"
2. Agradecer y explicar si es factible y cuándo (ser honesto)
3. Si se implementa, notificar al usuario: "Implementamos lo que pediste. ¿Qué te parece?"
4. Vincular al PWYW: "Mejoramos X que pediste — ¿esto cambia cuánto vale el sistema para ti?"

### 7.4 Señales de Alerta de Churn

| Señal | Acción |
|---|---|
| No ingresa al sistema en 5+ días | WhatsApp: "¿Todo bien? ¿Necesitas ayuda con algo?" |
| No registra ventas en 10+ días | WhatsApp: "¿Estás vendiendo por fuera del sistema? ¿Hay algo que te frena de usar el POS?" |
| Paga el mínimo ($5.000) 2 meses seguidos | Llamada: "¿Qué necesitarías para que el sistema te sirviera más?" |
| Crea un ticket de queja | Responder en menos de 24 horas. Prioridad máxima. |

---

## 8. Estrategia de Expansión

### 8.1 Referidos (WhatsApp-Based)

**No crear un programa formal de referidos.** Es overkill para 3 usuarios.

**En su lugar:**
- Cuando un usuario está satisfecho (paga >$20.000 y usa el sistema activamente):
  > "¿Conoces a otro cerero que tenga el mismo problema de no saber sus costos? Si me lo presentas por WhatsApp, le doy 1 mes gratis."
- El incentivo es simple y personal, no automatizado
- El referido entra al mismo flujo: demo → trial → onboarding → PWYW

### 8.2 Cuándo Introducir un Segundo Plan

No antes de tener 15+ usuarios pagando. Señales para crear tiers:

1. Usuarios claramente diferentes en uso (ej: uno usa solo POS, otro usa todo)
2. Requests recurrentes de features "pro" (reportes avanzados, múltiples sucursales)
3. Precio promedio PWYW estabilizado → usarlo como base del plan estándar

### 8.3 Expansión Geográfica

- **Fase 1 (meses 1-6):** Solo Cali. Presencial y WhatsApp.
- **Fase 2 (meses 6-12):** Valle del Cauca. Blog SEO empieza a traer tráfico orgánico de otras ciudades.
- **Fase 3 (año 2+):** Colombia. Si el blog y los videos funcionan, el tráfico será nacional.

No forzar la expansión. Dejar que el SEO y el boca a boca hagan su trabajo.

---

## 9. KPIs por Etapa del Funnel

### 9.1 Métricas Realistas para 90 Días

| Etapa | Métrica | Semana 4 | Semana 8 | Semana 12 |
|---|---|---|---|---|
| **Adquisición** | Prospectos contactados (total) | 100 | 200 | 300 |
| **Adquisición** | Tasa de respuesta | 10% | 12% | 15% |
| **Activación** | Trials iniciados (total) | 3 | 7 | 12 |
| **Activación** | Tasa de activación (3+ hitos) | 60% | 70% | 70% |
| **Conversión** | Usuarios pagando (total) | 0 | 2 | 5 |
| **Conversión** | Tasa trial→pago | — | 40% | 50% |
| **Ingresos** | Ingreso mensual total | $0 | $30.000 | $100.000+ |
| **Ingresos** | Precio promedio PWYW | — | $15.000 | $20.000 |
| **Retención** | Retención mes 1 | — | — | >80% |
| **SEO** | Artículos publicados | 0 | 2 | 6 |
| **SEO** | Impresiones Google Search Console | 0 | 100 | 500 |

### 9.2 Cuándo Declarar Product-Market Fit

PMF no es un número mágico. Para ChandeliERP, hay señales claras:

- **3+ usuarios pagan >$20.000/mes voluntariamente** durante 2+ meses consecutivos
- **Los usuarios usan el sistema sin que les recuerdes** (ingresan solos)
- **Al menos 1 usuario refiere a otro espontáneamente** (sin pedírselo)
- **El precio promedio PWYW sube** con el tiempo (no baja)
- **Los usuarios piden features nuevas** (señal de que quieren más, no menos)

Si estas señales no aparecen en 90 días, el problema no es el marketing — es el producto o el ICP.

---

## 10. Plan Operativo: 90 Días

### Semana 0: Prerrequisitos Técnicos (BLOQUEANTES)

Nada de marketing hasta que esto esté construido.

| # | Tarea | Esfuerzo | Prioridad | Detalle |
|---|---|---|---|---|
| 1 | **Landing page + Blog** en Vercel | 2-3 días | CRÍTICO | Landing con hero, features reales, video embed, CTA "Probar gratis 14 días", sección blog para SEO. Subdominio o ruta `/blog`. |
| 2 | **Signup self-service** | 2-3 días | CRÍTICO | Registro de tenant sin necesitar SuperAdmin. Formulario público → crea tenant + usuario admin automáticamente. |
| 3 | **Módulo de Soporte/PQRS** | 3-4 días | CRÍTICO | Tickets (Petición/Queja/Reclamo/Sugerencia/Soporte). Estados: ABIERTO→EN_PROCESO→RESUELTO/CERRADO. Prioridades. Vista usuario + vista admin. Historial de respuestas tipo chat. Dashboard de métricas. |
| 4 | **Onboarding wizard** | 2-3 días | ALTO | Tutorial de primeros pasos post-registro. Guía al usuario a: crear primer producto → crear primera receta → hacer primera venta. |
| 5 | **WhatsApp link flotante** | 0.5 día | MEDIO | Botón flotante en la app que abre WhatsApp con mensaje pre-llenado al founder. |
| 6 | **Video demo de 5 min** | 1 día | ALTO | Grabación + edición del flujo completo (ver guión en Sección 4, Canal 3). |

**Total semana 0:** ~12-15 días de desarrollo + 1 día para el video.

### Semanas 1-2: Lanzamiento Suave

**Objetivo:** Primeros 3-5 trials.

| Día | Acción | Tiempo |
|---|---|---|
| L | Publicar video demo en YouTube + landing page | 30 min |
| L | Publicar Reel corto (60s del video) en Instagram | 15 min |
| L-V | Enviar 5 mensajes de outreach personalizados/día | 1 hora/día |
| M | Primer post de Instagram (tipo "¿Sabías que...?") | 30 min |
| J | Segundo post de Instagram (tipo "Antes/Después") | 30 min |
| S | Review semanal: cuántos contactados, cuántos respondieron, cuántos trials | 30 min |

**Hitos semana 2:**
- 50 prospectos contactados
- 5-7 respuestas
- 2-3 trials con onboarding completado

### Semanas 3-4: SEO Kickoff

**Objetivo:** Publicar primeros 2 artículos del blog + mantener outreach.

| Día | Acción | Tiempo |
|---|---|---|
| L-V | 5 mensajes de outreach/día (no parar nunca) | 1 hora/día |
| M | Escribir y publicar artículo semanal del blog | 2-3 horas |
| M-J | 3 posts Instagram/semana | 30 min c/u |
| V | Configurar Google Search Console + Analytics 4 | 1 hora (una vez) |
| S | Review semanal | 30 min |

**Hitos semana 4:**
- 100 prospectos contactados totales
- 2 artículos publicados
- 3+ trials activos

### Semanas 5-8: Tracción

**Objetivo:** Primeros trials convirtiéndose. Primeros pagos PWYW.

| Semana | Foco |
|---|---|
| 5 | Onboarding de trials activos. Seguimiento día 3/7 por WhatsApp. Artículo #3. |
| 6 | Primeras conversaciones de conversión PWYW (trials de semana 1-2 ya cumplieron 14 días). Artículo #4. |
| 7 | Seguir outreach (nunca parar). Analizar qué funciona: ¿qué script genera más respuestas? ¿qué posts tienen más engagement? Artículo #5. |
| 8 | Ajustar lo que no funciona. Si 0 conversiones: investigar por qué (¿el producto? ¿el ICP? ¿el mensaje?). Artículo #6. |

**Hitos semana 8:**
- 200 prospectos contactados
- 6 artículos publicados
- 7+ trials totales
- 2+ usuarios pagando

### Semanas 9-12: Conversión y Primeros Ingresos

**Objetivo:** 5 usuarios pagando. Primer testimonial.

| Semana | Foco |
|---|---|
| 9 | Convertir trials pendientes. Pedir testimonial al usuario más activo. Artículo #7. |
| 10 | Publicar testimonial en landing page + Instagram. Usar en outreach: "Mira lo que dice [nombre] que también hace velas en Cali". Artículo #8. |
| 11 | Evaluar: ¿hay señales de PMF? ¿El precio promedio PWYW sube? ¿Los usuarios refieren? Blog. |
| 12 | Retrospectiva de 90 días. Documentar aprendizajes. Decidir si escalar outreach o pivotar. Blog. |

**Hitos semana 12:**
- 300 prospectos contactados
- 8+ artículos publicados
- 12+ trials totales
- 5+ usuarios pagando
- $100.000+ COP/mes de ingreso
- 1+ testimonial publicado
- Google Search Console mostrando impresiones

### Rutina Diaria del Founder

| Hora | Actividad | Duración |
|---|---|---|
| 8:00-9:00 | **Outreach:** Investigar 5 prospectos + enviar mensajes personalizados | 1 hora |
| 9:00-9:30 | **Soporte:** Responder WhatsApp de usuarios actuales + revisar tickets PQRS | 30 min |
| 9:30-12:00 | **Desarrollo:** Código (features, bugs, mejoras) | 2.5 horas |
| 12:00-13:00 | Almuerzo | — |
| 13:00-16:00 | **Desarrollo:** Código | 3 horas |
| 16:00-16:30 | **Contenido:** Preparar post de Instagram o avanzar artículo del blog | 30 min |
| 16:30-17:00 | **Follow-ups:** Responder DMs, seguimiento de trials, check-ins con usuarios | 30 min |

**Total marketing diario: ~2.5 horas** (outreach + soporte + contenido + follow-ups)
**Total desarrollo diario: ~5.5 horas**

### Herramientas Gratuitas

| Herramienta | Uso |
|---|---|
| Google Sheets | CRM manual (prospectos, trials, pagos), métricas |
| Google Search Console | SEO: indexación, queries, impresiones |
| Google Analytics 4 | Tráfico web y comportamiento |
| Google Meet | Videollamadas de onboarding |
| Loom / OBS Studio | Grabación de video demo |
| CapCut | Edición de video (Reels) |
| Canva (gratis) | Diseño de posts de Instagram |
| WhatsApp Business | Comunicación con prospectos y usuarios |
| Ubersuggest (gratis) | Investigación de keywords |

### Checklist Semanal de Ejecución

Cada sábado, revisar:

- [ ] ¿Envié 25+ mensajes de outreach esta semana?
- [ ] ¿Publiqué 3 posts en Instagram?
- [ ] ¿Publiqué 1 artículo en el blog? (a partir de semana 3)
- [ ] ¿Respondí todos los WhatsApp de usuarios en <24h?
- [ ] ¿Resolví todos los tickets PQRS abiertos?
- [ ] ¿Hice follow-up a los trials en día 3/7/12?
- [ ] ¿Actualicé mi hoja de métricas (prospectos, trials, pagos)?
- [ ] ¿Hay algún usuario que no ha entrado al sistema en 5+ días? → Contactar

---

## 11. Riesgos y Supuestos

### 11.1 Riesgos

| Riesgo | Probabilidad | Impacto | Plan B |
|---|---|---|---|
| **Nadie responde al outreach** | Media | Alto | Cambiar el script. Probar otro canal (Facebook groups). Ofrecer la demo gratis sin compromiso. |
| **Los trials no convierten** | Media | Alto | El problema es el producto o el ICP. Hacer entrevistas de salida: "¿Por qué no seguiste?" Iterar. |
| **Todos pagan el mínimo ($5.000)** | Media | Medio | Aceptable los primeros 3 meses. Si persiste, el producto no genera suficiente valor percibido. Mejorar features. |
| **El founder se quema (burnout)** | Alta | Crítico | Reducir outreach a 3/día en lugar de 5. No publicar blog en semanas de mucho desarrollo. Priorizar salud. |
| **Un usuario necesita DIAN** | Alta | Bajo | Ser honesto: "No tenemos DIAN aún. Lo que sí hacemos es..." No mentir ni prometer fechas. |
| **Competidor copia la idea** | Baja | Bajo | La ventaja no es la idea, es la ejecución y la relación 1-a-1 con cada cerero. Nadie puede copiar eso. |
| **SEO no genera tráfico** | Media | Bajo | El SEO es inversión a largo plazo. Si en 6 meses hay 0 tráfico, reevaluar keywords y calidad del contenido. |

### 11.2 Supuestos a Validar

| Supuesto | Cómo validarlo | Plazo |
|---|---|---|
| Los cereros de Cali no saben cuánto les cuesta cada vela | Preguntar en los primeros 10 outreach: "¿Sabes cuánto te cuesta producir tu vela más vendida?" | Semana 2 |
| Están dispuestos a usar software (vs cuaderno/Excel) | Tasa de aceptación de trials > 3% del outreach | Semana 4 |
| El costeo unitario es el "momento aha" real | Observar reacción durante onboarding. ¿Se sorprenden? ¿Dicen "no sabía que perdía tanto"? | Semana 4 |
| WhatsApp es mejor canal que email en Colombia | Tasa de respuesta WhatsApp vs cualquier otro canal | Semana 4 |
| $5.000 mínimo es suficiente para que paguen | Tasa de conversión trial→pago | Semana 8 |
| Los usuarios pagan más que el mínimo voluntariamente | Precio promedio PWYW > $10.000 | Semana 12 |
| El perfil "cerera en Cali" es el ICP correcto | Si 0 conversiones en Cali, probar otro perfil (jaboneros, cosméticos artesanales, panaderos) | Semana 12 |

---

> **Nota final:** Esta estrategia es un plan de 90 días, no un plan de 3 años. Cada semana debe reevaluarse basándose en datos reales, no en suposiciones. Si algo no funciona en 4 semanas, cambiarlo. Si algo funciona, duplicarlo. La agilidad es la única ventaja competitiva de un founder solo.
