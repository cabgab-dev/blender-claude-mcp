# Tu Paraíso — Estado del Proyecto

**Fecha última actualización:** 2026-03-24

## Resumen

Agente WhatsApp para el centro de estética **Tu Paraíso** (Roxana Cabrera).
Atiende clientes, consulta disponibilidad en Google Calendar y agenda turnos con confirmación de Roxana.

## Infraestructura

| Componente | Detalle |
|---|---|
| WhatsApp | Evolution API — instancia `TuParaiso` |
| Orquestador | n8n (mismo Docker de Gabo) |
| IA | Claude Sonnet (Anthropic API) |
| Calendario | Google Calendar (`primary` en pruebas → `tuparaisodd1679@gmail.com` en producción) |
| Estado de sesión | Redis (prefijo `tp:`) |

## Workflows n8n

| ID | Nombre | Estado |
|---|---|---|
| `RoZxWOIvXM6pke05` | TP-WF1 Gateway | ✅ Activo |
| `feC3Sfq1ly3LWFd1` | TP-WF2 Agente | ✅ Activo |
| `Ozq5advj8vaXgOxf` | TP-WF3 Confirmación Roxana | ✅ Activo |

### Webhooks

- Gateway recibe: `POST http://n8n:5678/webhook/tu-paraiso-webhook`
- Agente: `POST http://n8n:5678/webhook/tp-agente`
- Confirmación: `POST http://n8n:5678/webhook/tp-confirmacion`

## Flujo completo

```
Cliente WhatsApp (1165316398 en pruebas)
    ↓ mensaje
Evolution API → webhook → TP-WF1 Gateway
    ↓ buffer 30s
TP-WF2 Agente (Claude)
    ├─ conversación normal → respuesta al cliente
    ├─ necesita disponibilidad → consulta Google Calendar → oferta horarios
    └─ turno confirmado por cliente
          ↓
          Redis: guarda tp:pending:{chat_id}
          Notifica a Roxana (5491136922619 en pruebas)
          Cliente: "Tu turno está pendiente de confirmación"
               ↓
    Roxana responde SI o NO
          ↓
    TP-WF3 Confirmación
          ├─ SI → Crea evento en Google Calendar → Avisa al cliente ✅
          └─ NO → Limpia Redis → Avisa al cliente para reagendar
```

## Servicios y duraciones

| Servicio | Duración | Tolerancia | Slot total |
|---|---|---|---|
| Consulta Sin Cargo | 15 min | — | 15 min |
| Depilación Láser Soprano | 30 min | 15 min | 45 min |
| Masajes | 60 min | 15 min | 75 min |
| Limpieza de Cutis Profunda | 120 min | — | 120 min |
| Tratamientos Corporales | 120 min | — | 120 min |

## Horarios de atención

- **Lunes a Viernes:** 9:00–12:00 y 14:00–20:00
- **Sábados:** 14:00–18:00
- **Domingos:** cerrado

## Configuración para pruebas vs producción

| Parámetro | Pruebas | Producción |
|---|---|---|
| Número cliente | 1165316398 (Gabo) | número real del cliente |
| Número Roxana | 1136922619 (Gabo) | número real de Roxana |
| Google Calendar | `primary` (cuenta Gabo) | `tuparaisodd1679@gmail.com` |
| Credencial Calendar n8n | `Google Calendar ALFREDN8N` | nueva credencial Tu Paraíso |

## Pendiente

- [ ] Pruebas end-to-end
- [ ] Corregir bugs que aparezcan en las pruebas
- [ ] Crear credencial OAuth Google Calendar para `tuparaisodd1679@gmail.com`
- [ ] Swap de credenciales a las reales
- [ ] Migración a VPS
