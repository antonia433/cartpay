# CartPay - Sistema de Carrito Inteligente (Proyecto de Título)

Simulación completa del sistema CartPay: carrito con celdas de carga simuladas,
tablet con búsqueda, guía por voz, escaneo simulado, pago simulado y validación
de doble pesaje en la salida.

## Estructura del proyecto

```
cartpay/
├── backend/
│   ├── main.py          <- servidor FastAPI (toda la lógica)
│   └── requirements.txt
├── frontend/
│   └── index.html       <- pantalla de la tablet (HTML+JS)
└── README.md
```

## PASO 1 - Correr el backend en el PC

1. Se Abre VS Code → "Abrir carpeta" → se selecciona la carpeta `cartpay`.
2. Se Abre una terminal en VS Code (menú Terminal > Nueva Terminal).
3. Se Entra a la carpeta backend:
   ```
   cd backend
   ```
4. Se Crea un entorno virtual:
   ```
   python -m venv venv
   ```
5. Se debe Actívar:
   - Windows: `venv\Scripts\activate`
   - Mac/Linux: `source venv/bin/activate`
6. Luego Instalamos las dependencias:
   ```
   pip install -r requirements.txt
   ```
7. Luego Levantamos el servidor:
   ```
   uvicorn main:app --reload
   ```
8. se Verá algo como `Uvicorn running on http://127.0.0.1:8000`.
9. Se Abre en el navegador `http://127.0.0.1:8000/docs` — ahí hay que probar
   cada endpoint de la API directamente (Swagger, generado automático por FastAPI).

Se Deja esta terminal abierta y corriendo.

## PASO 2 - Abrir la tablet (frontend)

1. En VS Code, click derecho sobre `frontend/index.html` → "Open with Live Server"
   (con la extensión Live Server).
   - Si no tambein podemos con la extensión, simplemente es hacer doble clic en el archivo
     `index.html` para abrirlo en el navegador directamente.
2. Se abrirá la interfaz de la tablet en el navegador.
3. Flujo de prueba:
   - Clic en "Iniciar carrito".
   - Buscamos "leche" o "arroz" en el buscador → aparecerán resultados con precio
     y pasillo, y la voz te indicará dónde ir.
   - Copia el código que aparece al hacer clic en "Ver" (queda cargado en el
     campo "Código escaneado") y presionamos "Escanear" — esto simula pasar el
     producto por la cámara de la tablet.
   - Veremos el total y el peso (esperado vs celdas) actualizarse en vivo.
   - Presionamos "Pagar ahora" → elige Tarjeta o Celular → se genera una boleta
     con QR.
   - Presionamos "Ir al pórtico de salida" → "Medir peso y validar" → el sistema
     compara el peso pagado contra el peso real medido, igual que en tu diagrama.

### Códigos de prueba disponibles
| Código | Producto |
|---|---|
| 7801234560012 | Arroz Grado 1 1kg |
| 7801234560029 | Aceite Vegetal 900ml |
| 7801234560036 | Leche Entera 1L |
| 7801234560043 | Pan de Molde |
| 7801234560050 | Detergente 3kg |
| 7801234560067 | Bebida Cola 1.5L |
| 7801234560074 | Manzanas x kg |
| 7801234560081 | Papel Higiénico x4 |

## PASO 2.5 - Escaneo con cámara real (QR y código de barras)

Ahora la tablet puede leer de verdad con la cámara de tu notebook o celular
(librería `html5-qrcode`,).

**⚠️ Importante sobre navegadores:** por seguridad, los navegadores SOLO permiten
usar la cámara si la página se abre por `http://` (Live Server o el servidor),
no si abrimos el archivo `index.html` con doble clic (eso se abre como `file://`
y el navegador bloqueará la cámara). Por eso, para esta parte, usa sí o sí
"Open with Live Server" en VS Code (o el servidor en la nube del Paso 4).

**Cómo probarlo:**
1. Presionamos el botón **"📷 Escanear con cámara"** — el navegador te pedirá
   permiso para usar la cámara, acéptalo.
2. Apuntamos la cámara a un código QR o código de barras.
3. Para probar sin productos reales, generariamos un QR gratis en
   https://www.qr-code-generator.com/ con el texto `7801234560012`
   (o cualquiera de los códigos de la tabla de abajo) y se lo muéstraremos a la cámara
   desde el celular o impreso.
4. Apenas lo detecta, agregamos automáticamente el producto al carrito (igual que
   si lo hicieramos manual).
5. Presionamos **"⏹ Detener cámara"** cuando terminemos de escanear.

**Si quieremos usar códigos de barras de productos reales de tu casa:** abre
`backend/main.py`, buscariamos el diccionario `PRODUCTOS`, y agregariamos una línea nueva
con el código de barras real del producto (los 13 números que están bajo el
código de barras) y el nombre/precio/peso que quisieramos simular. Así, al escanear
el producto real con la cámara, el sistema lo va a reconocer.

## PASO 3 - Simular una alerta de robo/diferencia de peso

Para demostrar la alerta en nuestra defensa: agregamos productos, paga, ve al pórtico
de salida, y ANTES de "Medir peso y validar" agrega otro producto (sin pagarlo)
usando el buscador y escaneo. Esto hará que el peso real no calce con lo pagado
y el sistema mostrará la alerta roja, tal como en tu diagrama técnico.

## PASO 4 - Subir el backend a la nube ( para que sea "un servidor real")

Esto le da mucho valor a nuestra propuesta de título: no dependemos del PC.

1. Creamos una cuenta gratis en https://render.com (o https://railway.app).
2. Subimos nuestro proyecto a GitHub (creamos un repo y subimos la carpeta `cartpay`).
3. En Render: "New" → "Web Service" → conectamos nuestro repo de GitHub.
4. Configuración:
   - Root directory: `backend`
   - Build command: `pip install -r requirements.txt`
   - Start command: `uvicorn main:app --host 0.0.0.0 --port 10000`
5. Deploy. Render nos dara dará una URL pública, por ejemplo:
   `https://cartpay-backend.onrender.com`
6. En `frontend/index.html`, cambiamos la línea:
   ```js
   const API = "http://127.0.0.1:8000";
   ```
   por:
   ```js
   const API = "https://cartpay-backend.onrender.com";
   ```
7. Ahora en la tablet (el HTML) se puede abrir desde cualquier lado — incluso desde
   el celular — y va a hablar con nustro servidor en la nube.
