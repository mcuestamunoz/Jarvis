# Engineer note — Bench before silicon; software continues (2026-09-24)

**Author:** Cursor (capture of Engineer evaluation)  
**Trigger:** Engineer 2026-09-24: remaining parts still to buy/arrive; **test bench + soldering** before mounting/connecting the craft. Do **not** treat C30 flash as AHORA. List the future hardware steps; keep implementing **software that does not need the bench**.

**Tip remains:** **`v0.5.27`**. C30 IC stays written, **parked until bench**.

---

## Lock (process)

```text
Pieces + bench + solder  →  then mount / connect / first power
Software that needs no pin  →  keep going now (one front at a time)
C30 DFU / overwrite Betaflight  →  parked until the bench is boringly safe
```

- The HGLRC **F460 stack already on the desk** (FC F405 + ESC 60 A) is **not** a reason to flash Jarvis today.
- C30 flash *technically* only needs the FC + USB + BOOT. That still **overwrites Betaflight**. Without a bench and a restore path you trust, keep **HGLRCF405V2** on the chip.
- **FC 8S vs ESC 6S:** the stack limit is **6S**. Do not buy an 8S pack “because the FC says 8S”.

---

## A. When we mount / connect (hardware campaign — parked)

Do these **in order**. Props off until step 10.

### A0. Banco (before any solder on flight parts)

1. Mesa no inflamable, bolsa LiPo, gafas, extractor o ventana.  
2. **Smoke stopper** (o fusible) en el positivo de la batería para el primer encendido.  
3. Hierro de soldar + flux + estaño; **practicar en chatarra**, no en la FC.  
4. USB al Mac; Betaflight Configurator instalado.  
5. Hélices **fuera** del área de trabajo hasta el paso 10.

### A1. Piezas que aún faltan (típico; ajustar a lo que ya tengas)

| Pieza | Para qué | Nota honesta |
|---|---|---|
| Frame | Brazos + stack | El F460 es FC+ESC, no el cuadro |
| 4 motores | Empuje | Calibre compatible 6S / ESC 60 A |
| Hélices | Después de probar motores | No montarlas en el primer power |
| LiPo **6S** + cargador | Energía | ESC es 6S; no 8S |
| RX ELRS | Sticks → UART2 | Manual HGLRC: UART2 = RX |
| Cables / XT60 / bridas | Energía y orden | |
| (Opcional) cámara / VTX | FPV | UART1 = VTX en el mismo manual |

### A2. Montaje mecánico

1. Motores en brazos (sin hélices).  
2. Stack FC+ESC en el frame (standoffs). Orientación del gyro: se calibra luego en BF.  
3. RX en el frame, antena lejos de VTX si hay VTX.

### A3. Soldadura / conexión (señales citadas HGLRCF405V2)

| Qué | Dónde | No es |
|---|---|---|
| Motores 1–4 | ESC pads / M1–M4 · BF `MOTOR 1..4` = **C06 C07 C08 C09** | DShot de Jarvis (aún no existe) |
| RX CRSF | **UART2** (TX/RX A02/A03) | ELRS “ya vive en Jarvis” |
| Telemetría ESC | **UART5** según manual HGLRC | USART de nuestro stub |
| LED de estado | **PC13** (C30, parked) | Tira LED **PB1** |
| Batería | Pads ESC + smoke stopper | Encender a 8S |

### A4. Primer power (Betaflight, no Jarvis)

1. USB solo → Configurator → target **HGLRCF405V2** (confirmar gyro ICM42688P).  
2. Batería a través del smoke stopper, hélices **off**.  
3. Motors tab: **un motor, poco throttle, mano lejos**. Dirección; si no, swap wires o `Reverse`.  
4. Receiver: sticks AETR. Failsafe BF armado.  
5. Baro / OSD si aplica.  
6. **Hélices** solo cuando 3–4 son aburridos y repetibles.  
7. Primer hover es **Betaflight**. Jarvis no sustituye eso.

### A5. Jarvis en la placa (solo cuando A0–A4 aburren)

1. C30: DFU del `fc_mcu_stub.bin` → LED **PC13**. Restaurar = reflashear **HGLRCF405V2**.  
2. Más tarde, Buys de DShot-en-pin / USART-en-chip — cada uno con IC, hélices off.

---

## B. Software now (no pin, no banco)

Already landed on the Mac (`v0.5.27`): Intent/Safety stub · FC ladder + `step` · AETR · `EscOutput` sim · RC hold · UART loopback · cited FLASH map · host CRSF (no dongle required).

**Allowed next Buys** (one at a time; Cursor IC → ★ → Claude). None of these need solder:

| Front | Qué demuestra | Sigue siendo imposible |
|---|---|---|
| **DShot encode (recomendado)** | Fuerza → trama DShot en RAM (checksum, 150/300/600 como *número de protocolo*, no como pin) | GPIO, timer, ESC girando |
| SPI / IMU byte stub | Mismo patrón que C28 UART: enchufe SPI, loopback o fixture ICM42688P | Bus real del gyro |
| Deepen C20 policy | Más aux / kinds de Authority | Safety execute |
| Host sim del tick | `step` + hold + mixer en pytest más denso | Planta 6-DoF realista ≠ vuelo |
| craft↔FS | Perfil de *este* quad ligado al craft | Acoplar Continuity al firmware |

**Forbidden until bench + explicit IC:** C30 flash as AHORA · DShot *wire* · USART ISR · Safety execute · motors.

**C30 IC:** [implementation_contract_fase_c_mcu_flash_observable_b1.md](implementation_contract_fase_c_mcu_flash_observable_b1.md) — **READY on paper, PARKED in cola** until the Engineer opens silicon.

---

## C. PRIORIDAD blurb

```text
Fase C: C29 B1 CLOSED @ v0.5.27. C30 flash PARKED until bench+solder.
Software continues on the Mac — next IC TBD (recommended: DShot encode,
not pin). Hardware campaign A0–A5 is the future mount/connect list, not
today's Buy.
```
