# 🍽 Menú del comedor — Palomeras Bajas

El colegio publica cada mes el menú del comedor en un PDF
([menús del mes en curso](https://palomerasbajas.org/wp/menus-mes-en-curso/)).
Este proyecto lo convierte, sin que tengas que hacer nada cada mes, en:

- **Una web** cómoda en el móvil con lo que queda del mes, empezando por hoy. Tiene los 9 menús del
  colegio (orientativo, sin huevo, sin lácteos, sin frutos secos, sin pescado, celíacos,
  multialérgico, musulmán y musulmán sin carne): se elige en un desplegable y cada móvil recuerda el último.
- **Un calendario por menú** al que te suscribes una vez (iPhone, Mac, Google Calendar…) y que se
  actualiza solo. Cada día de cole aparece como un evento de todo el día con los platos.
- **Avisos en un canal público de Telegram** al que cualquier familia puede unirse (con el menú orientativo):
  - **Domingo por la tarde:** el menú de toda la semana, para planificar la compra.
  - **De lunes a jueves por la tarde:** lo que comen mañana y qué conviene evitar en la cena.

```
🍽 Mañana (mié 7) en el comedor:
• Patatas guisadas con magro
• Huevos cocidos con tomate y ensalada
• Fruta de temporada

Para la cena de mañana, mejor evitar: 🥩 carne · 🥔 patata · 🥚 huevo
```

Todo funciona gratis con GitHub (GitHub Actions + GitHub Pages). No hace falta tener
ningún ordenador encendido.

> 📲 **¿Tu peque va a Palomeras Bajas y solo quieres los avisos?** No tienes que montar nada:
> entra en la web del menú y pulsa **Avisos en Telegram** para unirte al canal.

> ⚠️ Todo se genera automáticamente a partir de los PDF del colegio y puede tener errores.
> **Si hay alergias, el PDF oficial manda.** La web lo recuerda y enlaza al PDF de cada menú.

---

## Cómo funciona

```
Del 27 al 7 de cada mes, cada mañana, y el resto del mes, los lunes (GitHub Actions)
  1. Descarga los 9 PDF del colegio (siempre están en la misma dirección).
  2. Los lee con pdfplumber y guarda cada mes en datos/MENU/AAAA-MM.json.
  3. Si ha cambiado algo, genera la web y un calendario por menú (orientativo.ics,
     sin-huevo.ics…) y los publica en GitHub Pages.
  4. Si hay mes nuevo del menú orientativo, avisa por Telegram.

Cada tarde (GitHub Actions)
  5. Envía el aviso del día (o de la semana, los domingos) por Telegram.
```

Cada plato se clasifica en grupos (pescado, huevo, carne, legumbres, pasta, arroz, patata)
para el aviso de "mejor evitar en la cena". Las palabras están en
[`comedor/categorias.py`](comedor/categorias.py) y es fácil añadir más.

---

## Montarlo para tu familia (unos 15 minutos)

Necesitas una cuenta de GitHub (gratis) y Telegram.

### 1. Crea tu copia del proyecto

1. Pulsa el botón verde **Use this template → Create a new repository** (arriba en esta página).
2. Ponle un nombre (por ejemplo `menu-comedor`) y déjalo como **Public**
   (GitHub Pages es gratis en repositorios públicos; en el repositorio no hay datos personales).

### 2. Activa la web (GitHub Pages)

1. En tu repositorio: **Settings → Pages**.
2. En **Source**, elige **GitHub Actions**.

### 3. Primera ejecución

1. Pestaña **Actions**. Si te lo pide, pulsa el botón para activar los workflows.
2. Elige **Actualizar menú** → **Run workflow**.
3. Cuando termine (≈1 minuto) tendrás la web en `https://TU-USUARIO.github.io/NOMBRE-DEL-REPO/`.

### 4. Suscríbete al calendario

- **Desde el iPhone (lo más fácil):** abre la web en Safari, elige tu menú en el desplegable y pulsa
  **📅 Añadir al calendario** → **Suscribirse**.
- **A mano:** Ajustes → Calendario → Cuentas → Añadir cuenta → Otra → **Añadir calendario suscrito**, y pega
  `https://TU-USUARIO.github.io/NOMBRE-DEL-REPO/orientativo.ics` (o `sin-huevo.ics`, `celiacos.ics`…;
  los nombres están en [`comedor/menus.py`](comedor/menus.py)).
- **Google Calendar:** Otros calendarios → **+** → Desde URL, con la misma dirección.

Cada miembro de la familia se suscribe desde su propio móvil.

> Los calendarios suscritos del iPhone no suelen respetar alarmas, por eso los avisos van por Telegram.

### 5. Avisos por Telegram (canal público)

Los avisos se publican en un **canal** de Telegram: solo el bot puede escribir, cualquiera puede
unirse con el enlace, y los miembros no ven quién más está (así se protege la privacidad de cada familia).
Cada persona puede silenciarlo o salirse cuando quiera.

**a) Crea el bot**

1. En Telegram, habla con [@BotFather](https://t.me/BotFather) (tiene la marca azul de verificado) y envía `/newbot`.
2. Elige un nombre (p. ej. "Menú comedor") y un usuario acabado en `bot` (p. ej. `menu_comedor_palomeras_bot`).
3. BotFather te da un **token** del estilo `123456789:ABCdef...`. No lo compartas con nadie
   (si se filtra, envía `/revoke` a @BotFather para anularlo).

**b) Crea el canal**

1. En Telegram: **Nuevo canal**. Ponle nombre (p. ej. "Menú comedor Palomeras Bajas") y una descripción.
2. Elige **Canal público** y un enlace, p. ej. `t.me/menucomedorpalomeras`.
3. En el canal: **Administradores → Añadir administrador**, busca tu bot y déjale solo el permiso
   de **publicar mensajes**.

**c) Guárdalo en GitHub**

Desde la terminal (pide el valor sin mostrarlo en pantalla):

```bash
gh secret set TELEGRAM_BOT_TOKEN --repo TU-USUARIO/NOMBRE-DEL-REPO
gh secret set TELEGRAM_CHAT_ID --repo TU-USUARIO/NOMBRE-DEL-REPO
gh variable set TELEGRAM_CANAL --repo TU-USUARIO/NOMBRE-DEL-REPO
```

O en el navegador, en tu repositorio: **Settings → Secrets and variables → Actions**:

| Dónde       | Nombre               | Valor                                             |
| ----------- | -------------------- | ------------------------------------------------- |
| *Secrets*   | `TELEGRAM_BOT_TOKEN` | el token de BotFather                             |
| *Secrets*   | `TELEGRAM_CHAT_ID`   | el canal con @, p. ej. `@menucomedorpalomeras`    |
| *Variables* | `TELEGRAM_CANAL`     | el canal sin @, p. ej. `menucomedorpalomeras` (pone el botón "📲 Avisos en Telegram" en la web) |

**d) Prueba:** Actions → **Avisos por Telegram** → **Run workflow** → modo `semana`.
Debería aparecer el menú de la semana en el canal. Después, lanza también **Actualizar menú**
para que aparezca el botón de Telegram en la web.

**e) Compártelo:** únete al canal y pasa el enlace (o el de la web) al resto de familias.

> **¿Prefieres un grupo privado solo para tu familia?** También funciona: crea el grupo, añade el bot,
> escribe `/start@usuario_de_tu_bot` en el grupo y abre `https://api.telegram.org/botTU_TOKEN/getUpdates`
> en el navegador. El número que aparece en `"chat":{"id":-100...` (con el signo menos) es el
> `TELEGRAM_CHAT_ID`. En ese caso no hace falta `TELEGRAM_CANAL`.

¡Listo! A partir de ahora todo es automático.

**¿Es seguro guardar el token en GitHub?** Sí, es lo habitual:

- Los *secrets* se guardan cifrados y nadie puede volver a verlos, ni siquiera tú (solo cambiarlos o borrarlos).
  Que el repositorio sea público no los hace públicos.
- Quien copie la plantilla o proponga cambios (*pull requests*) no tiene acceso a tus secretos.
- Si alguno aparece en los registros de Actions, GitHub lo tapa con `***`.
- Solo el paso que envía el mensaje recibe los secretos, y los workflows usan únicamente acciones
  oficiales de GitHub, fijadas a una versión concreta.
- Lo peor que se puede hacer con el token es enviar mensajes como tu bot en los chats donde esté
  (en un canal público, eso incluye a todas las familias que lo siguen). Por eso dale al bot solo el
  permiso de publicar. Si crees que se ha filtrado, envía `/revoke` a @BotFather y pon el nuevo token
  en GitHub.
- No des permiso de escritura en tu repositorio a nadie en quien no confíes.

---

## Personalizar

Todo se cambia desde **Settings → Secrets and variables → Actions → Variables** (sin tocar código):

| Variable            | Para qué                                              | Por defecto |
| ------------------- | ----------------------------------------------------- | ----------- |
| `MENU_AVISOS`       | Menú del que se envían los avisos de Telegram (p. ej. `sin-huevo`) | `orientativo` |
| `NOMBRE_CALENDARIO` | Nombre del calendario en el móvil                     | `Comedor Palomeras` |
| `URL_WEB`           | Dirección de la web, si usas un dominio propio        | la de GitHub Pages |
| `TELEGRAM_CANAL`    | Canal público de Telegram (sin @) para el botón de la web | sin botón |

**Menús:** la lista está en [`comedor/menus.py`](comedor/menus.py). Si el colegio añade o quita
alguno, basta con cambiar esa lista. Todos usan la misma plantilla y se leen bien (probado con los de
octubre de 2026). Si uno falla, los demás se actualizan igualmente y GitHub te avisa por email.

**Cuándo se busca el menú nuevo:** el colegio lo cambia el último día de cada mes, "salvo algún
retraso". Por eso se comprueba a diario del 27 al 7 y los lunes el resto del mes (por si corrigen
algo). Se cambia en [`.github/workflows/actualizar.yml`](.github/workflows/actualizar.yml).
Si tienes prisa, **Actions → Actualizar menú → Run workflow** lo comprueba al momento.

**Horarios de los avisos:** cambia la línea `cron` de
[`.github/workflows/avisos.yml`](.github/workflows/avisos.yml). La hora está en UTC
(en Madrid: +2 h en verano, +1 h en invierno). [crontab.guru](https://crontab.guru) ayuda a escribirla.
GitHub puede retrasar los avisos programados unos minutos.

**¿Prefieres que el aviso diario sea por la mañana sobre el día de hoy?** Cambia el `cron` a una
hora de la mañana de lunes a viernes (`"0 6 * * 1-5"`) y la última línea a
`python -m comedor avisar hoy`.

**¿Y WhatsApp?** Enviar mensajes automáticos a WhatsApp requiere la API de empresas (o servicios de pago
como Twilio), así que hemos elegido Telegram, que es gratis y se configura en cinco minutos.

---

## Probarlo en tu ordenador

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python -m comedor actualizar             # descarga y lee los PDF del mes
python -m comedor actualizar --menu sin-huevo   # solo un menú
python -m comedor avisar semana          # muestra el aviso semanal por pantalla
python -m comedor avisar --fecha 2026-10-06   # como si hoy fuera esa fecha
python -m pytest                         # pruebas
```

Sin `TELEGRAM_BOT_TOKEN` y `TELEGRAM_CHAT_ID`, los avisos solo se muestran por pantalla.
La web se genera en `sitio/`; para verla: `python -m http.server -d sitio` y abre <http://localhost:8000>.

---

## Si algo falla

- **GitHub te manda un email de que "Actualizar menú" ha fallado.** Lo más probable es que el colegio
  haya cambiado el formato del PDF o que su web estuviera caída ese día. Mira el error en la pestaña
  **Actions**. Si es el formato, el lector está en [`comedor/parser.py`](comedor/parser.py); añade el PDF
  nuevo a `tests/pdf/` y una prueba en [`tests/test_parser.py`](tests/test_parser.py).
- **Un plato sale mal.** Puedes corregirlo a mano en `datos/MENU/AAAA-MM.json` (se respeta hasta que el
  colegio cambie el PDF de ese mes).
- **Después del verano no llega nada.** GitHub desactiva las tareas programadas de los repositorios
  públicos tras 60 días sin cambios. En septiembre, entra en **Actions** y vuelve a activarlas.

---

Hecho por familias del cole, para familias del cole. Si lo mejoras, ¡comparte los cambios!
Licencia [MIT](LICENSE).
