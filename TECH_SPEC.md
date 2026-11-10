# Technická specifikace a integrační manuál: xcc2 Frontend

Tento dokument obsahuje kompletní technické detaily, reverzně analyzované rozhraní API a architekturu pro vývoj moderní webové aplikace komunikující s PLC backendem **xcc** běžícím na adrese **`http://192.168.0.122`**.

---

## 1. Přehled systému a architektura

Backend je průmyslový řídicí systém (PLC/Java controller) určený primárně pro:
* **Tepelná čerpadla (TČ)** – kaskády jednotek (1–4 a více), kompresory, invertory, provozní stavy.
* **Topné okruhy a regulaci** – ekvitermní křivky, požadované a reálné teploty, přepínání topení/chlazení.
* **Přípravu teplé užitkové vody (TUV)** – ohřev, cirkulace, dezinfekce.
* **Fotovoltaiku a zónovou regulaci (FVE, VZT, multizóny)**.
* **Diagnostiku a alarmy** – detekce a resetování systémových chyb.
* **Konfiguraci a správu modulů** – dynamická stromová hierarchie komponent a proměnných.

Původní frontend byl monolitický React SPA bundle (React 18 + React-Bootstrap + Webpack). Nová aplikace jej nahradí moderním frontendovým stackem (např. **Vite + React 19 + TypeScript + Tailwind / shadcn/ui + TanStack Query**).

---

## 2. Síťové nastavení a Base URL

* **Backend IP adresa:** `192.168.0.122`
* **Výchozí port:** `80` (HTTP)
* **Base URL kontexty:**
  1. **Standardní přístup:** `/` (všechny endpointy začínají v kořeni, např. `/functions.json`, `/getData.json`).
  2. **PLC subpath přístup:** Pokud URL obsahuje `/plc/`, základní cesta aplikace se adaptuje na `/plc/<nazev_app>/` a odhlašovací cesta na `/plc/`.

### Vývojový proxy server (Vite)
Pro lokální vývoj je nezbytné nakonfigurovat reverse proxy, aby se zamezilo problémům s CORS a umožnilo správné předávání session cookies:

```typescript
// vite.config.ts
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '^/.*\\.json': {
        target: 'http://192.168.0.122',
        changeOrigin: true,
        secure: false,
      },
      '/files': {
        target: 'http://192.168.0.122',
        changeOrigin: true,
        secure: false,
      }
    }
  }
});
```

---

## 3. Autentizace, autorizace a session

Systém podporuje dva stupně oprávnění: běžný uživatel a **administrátor** (`admin`).

1. **Přihlášení:**
   - Volá se `POST /login.json?login={username}&pass={password}`.
   - Po úspěšném přihlášení vrací backend uživatelský profil v JSON.
   - Backend nastavuje HTTP cookies:
     - `logged=<username>` – identifikátor přihlášeného uživatele.
     - `jpar=true` – příznak administrátorského oprávnění (zobrazuje sekci `/config`).
2. **Kontrola existující session:**
   - Aplikace kontroluje `document.cookie`:
     - Přítomnost `logged=` značí aktivní session.
     - Přítomnost `jpar=true` nastavuje `admin: true`.
   - V lokálním úložišti se profil cachuje pod klíčem `xcclogged`:
     ```json
     {
       "login": "admin",
       "admin": true,
       "coo": true
     }
     ```
3. **Odhlášení:**
   - Volá se `GET /logout.json` (případně přesměrování na zjištěný `logoutPath`).
   - Smažou se všechny klíče z `localStorage` začínající prefixem `xcc` (`xcc*`).
4. **Zpracování neautorizovaného přístupu (HTTP 401):**
   - Všechny API požadavky ověřují status odpovědi. Při kódu 401 dojde k vyvolání přihlašovacího dialogu nebo reloadu stránky.

---

## 4. Kompletní specifikace API (22 endpointů)

Všechny HTTP požadavky posílají hlavičky:
```http
Accept: application/json
Content-Type: application/json; charset=utf-8
```
A pracují v režimu `credentials: "same-origin"` (případně `"include"` při cross-origin požadavcích).

---

### 4.1 Autentizace a session

#### `POST /login.json?login={user}&pass={pass}`
* **Metoda:** `POST`
* **Query parametry:**
  * `login`: uživatelské jméno
  * `pass`: heslo
* **Odpověď:** JSON s daty o přihlášeném uživateli.
* **Chybový stav:** HTTP 401 Unauthorized při neplatných údajích.

#### `GET /logout.json`
* **Metoda:** `GET`
* **Popis:** Ukončí aktivní relaci na straně serveru a zneplatní session cookies.

---

### 4.2 Komponenty a funkční bloky

#### `GET /functions.json`
* **Metoda:** `GET`
* **Query parametry:**
  * `status` (flag, např. `?status`): zahrnout aktuální stavy komponent.
  * `layout` (flag, `&layout`): zahrnout rozložení / layout definice.
  * `extended` (flag, `&extended`): rozšířené metainformace.
* **Odpověď:** Pole nebo mapa instancí funkčních komponent:
  ```json
  [
    {
      "id": "1",
      "name": "Topný okruh 1",
      "TYPE": "xcc.component.TopnyOkruh",
      "status": {
        "on": true,
        "reqTemp": 21.5,
        "actTemp": 21.3,
        "operationMode": "HEAT"
      }
    }
  ]
  ```
  *Poznámka:* Klient indexuje pole do mapy podle klíče `id`.

#### `POST /addFunction.json?type={type}&name={name}[&config={config}]`
* **Metoda:** `POST`
* **Query parametry:**
  * `type`: plný název třídy (např. `xcc.component.TopnyOkruh`)
  * `name`: název komponenty zadaný uživatelem
  * `config` *(volitelné)*: přednastavená konfigurace
* **Popis:** Vytvoří novou instanci komponenty.

#### `POST /removeFunction.json?id={id}`
* **Metoda:** `POST`
* **Query parametry:** `id`: identifikátor odstraňované komponenty.

---

### 4.3 Práce se stavem a daty (Data Masking & Projection)

#### `POST /getData.json`
* **Metoda:** `POST`
* **Query parametry:** `?status` (volitelně `&layout`, `&extended`)
* **Tělo požadavku (JSON):** Projekční maska vlastností (vyžádá pouze potřebná data):
  ```json
  {
    "1": {
      "name": 1,
      "icon": 1,
      "status": {
        "reqTemp": 1,
        "actTemp": 1
      }
    }
  }
  ```
* **Odpověď:** Strom dat odpovídající vyžádané masce:
  ```json
  {
    "1": {
      "name": "Topný okruh 1",
      "icon": 61,
      "status": {
        "reqTemp": 22.0,
        "actTemp": 21.8
      }
    }
  }
  ```

#### `POST /saveData.json`
* **Metoda:** `POST`
* **Tělo požadavku (JSON):** Objekt nebo pole změn:
  ```json
  [
    {
      "id": "1",
      "propPath": ["status", "reqTemp"],
      "value": 22.5
    }
  ]
  ```
  Případně uložení konfigurace celého layoutu:
  ```json
  {
    "id": "globalId",
    "propPath": ["webLayout"],
    "fromJson": { ... }
  }
  ```

#### `POST /getStates.json`
* **Metoda:** `POST`
* **Query parametry:**
  * `?all` – vrátí stavy a chyby všech komponent.
  * `?idComp={id}` – vrátí stav konkrétní komponenty.
* **Tělo požadavku:** `null` (prázdné tělo).
* **Popis:** Využíváno pro diagnostiku a tabulku chyb na `/error`.

---

### 4.4 Moduly a reflexe typů

#### `GET /modules.json`
* **Metoda:** `GET`
* **Popis:** Seznam fyzických a logických modulů (I/O karty, převodníky, RS485).
* **Struktura:**
  ```json
  [
    {
      "id": "mod1",
      "name": "Modbus Master 1",
      "type": "xcc.module.Modbus"
    }
  ]
  ```

#### `GET /module.json?id={id}[&methods]`
* **Metoda:** `GET`
* **Query parametry:**
  * `id`: ID modulu
  * `methods` *(flag)*: pokud je uveden, backend vrátí i seznam volatelných metod.

#### `POST /changeModule.json`
* **Metoda:** `POST`
* **Tělo požadavku:** Změněná data modulu pro uložení.

#### `GET /types.json`
* **Metoda:** `GET`
* **Popis:** Vrací katalog dostupných typů a tříd v PLC:
  ```json
  [
    {
      "class": "xcc.component.TopnyOkruh",
      "simple": "topnyOkruh",
      "name": "Topný okruh",
      "component": true
    }
  ]
  ```

#### `GET /typeCfgs.json?type={type}`
* **Metoda:** `GET`
* **Query parametry:** `type`: plný název typu.
* **Popis:** Vrací schéma konfiguračních polí a výchozích hodnot.

---

### 4.5 Volání metod a práce s poli

#### `POST /runMethod.json`
* **Metoda:** `POST`
* **Popis:** Slouží k vyvolání vzdálené procedury (RPC) na komponentě nebo modulu (např. restart, kvitace chyb, spuštění odtávání).
* **Volání na komponentě:**
  ```json
  {
    "id": "1",
    "propPath": ["subsystem"],
    "method": "resetAlarm",
    "parameters": []
  }
  ```
* **Volání na modulu:**
  ```json
  {
    "module": true,
    "id": "mod1",
    "method": "reconnect",
    "parameters": []
  }
  ```

#### `POST /addToArray.json`
* **Metoda:** `POST`
* **Tělo požadavku:**
  ```json
  {
    "id": "1",
    "propPath": ["schedules", "timePrograms"]
  }
  ```

#### `POST /removeFromArray.json`
* **Metoda:** `POST`
* **Tělo požadavku:**
  ```json
  {
    "id": "1",
    "propPath": ["schedules", "timePrograms"]
  }
  ```

---

### 4.6 Konfigurace, zálohy a soubory

#### `GET /getConfigs.json?user&service&modules`
* **Metoda:** `GET`
* **Popis:** Seznam uložených profilů nastavení.

#### `GET /saveConfig.json?name={name}[&user][&service][&modules]`
* **Metoda:** `GET`
* **Popis:** Uloží aktuální stav systému do pojmenovaného profilu.

#### `GET /loadConfig.json?user={user}&service={service}[&modules={modules}]`
* **Metoda:** `GET`
* **Popis:** Načte zvolenou konfiguraci do systému.

#### `POST /upload.json?file={filename}`
* **Metoda:** `POST`
* **Tělo požadavku:** Binární nebo JSON obsah souboru.

#### `POST /saveObject.json?id={id}`
* **Tělo požadavku:** `{ "toResponse": boolean, "file": string, "id": string, "propPath": [] }`

#### `POST /loadObject.json?file={file}&id={id}`
* **Tělo požadavku:** `{ "file": string, "data": any, "id": string, "propPath": [] }`

---

## 5. Mechanismus synchronizace dat (Data Engine & Polling)

1. **Cyklus vyčítání (Polling):**
   * Výchozí interval je **2 000 ms** (2 sekundy).
   * Každý aktivní pohled (stránka) vygeneruje masku požadovaných proměnných pro zobrazené komponenty:
     ```typescript
     function buildPropertyMask(blocks: Block[]): Record<string, any> {
       const mask: Record<string, any> = { name: 1, icon: 1 };
       for (const block of blocks) {
         if (block.prop) addPath(mask, block.prop);
         if (block.propRun) addPath(mask, block.propRun);
         for (const row of block.rows) {
           if (row.prop) addPath(mask, row.prop);
           for (const comp of row.comps ?? []) {
             if (comp.prop) addPath(mask, comp.prop);
           }
         }
       }
       return mask;
     }
     ```
   * Klient odešle `POST /getData.json?status` s tímto tělem.
2. **Bufferování a odesílání změn (Optimistic Write Queue):**
   * Když uživatel změní hodnotu (např. posuvník teploty, přepínač):
     1. Hodnota se okamžitě projeví v UI (optimistický update).
     2. Změna se zařadí do fronty změn `yp = [{ id, propPath, value }]`.
     3. Běžící polling se odloží (na 100 ms), aby nekolidoval se zápisem.
     4. Fronta se odešle přes `POST /saveData.json`.
     5. Po dokončení zápisu se obnoví standardní 2s polling.

---

## 6. Podporované typy komponent (`xcc.component.*`)

Aplikace pracuje s těmito základními třídami komponent:

| Typ třídy | Význam v systému | Klíčové parametry / vlastnosti |
|---|---|---|
| `xcc.component.TopnyOkruh` | Topný / chladicí okruh | `on`, `reqTemp`, `actTemp`, `operationMode` (`HEAT`/`COOL`), `natop` |
| `xcc.component.Tuv` | Příprava teplé vody | `on`, `reqTemp`, `actTemp`, `cirkulace`, `antiledionella` |
| `xcc.component.HeatPump` | Jednotka tepelného čerpadla | `status`, kompresor, provozní frekvence, průtok, tlaky |
| `xcc.component.Regulator` | Ekvitermní regulátor | Křivka, vliv prostoru, limity, útlumy |
| `xcc.component.TempOut` | Venkovní snímač teploty | `actTemp`, filtrovaná teplota |
| `xcc.component.Global` | Globální systémový stav | `idGlobal`, režim celé kotelny, webLayout, čas PLC |
| `xcc.component.Inverter` | Frekvenční měnič kompresoru | Skutečná/požadovaná frekvence, proud, chybové kódy |
| `xcc.component.Logger` | Datalogger | Intervaly logování, sledované signály, historie |
| `xcc.component.ModbusSlave` | Komunikace Modbus RTU/TCP | Registry, adresace, komunikační status |
| `xcc.component.Vzt` | Vzduchotechnika / rekuperace | Výkon ventilátorů, bypass, teploty |
| `xcc.component.Multizona` | Vícezónová regulace | Podokruhy, prostorové termostaty |

### Typy UI prvků (Widgety v řádcích):
* `switch` – binární přepínač (Zap/Vyp).
* `choice` – výběr z možností (např. Topení / Chlazení / Auto).
* `number` – číselná hodnota s krokem a limity (např. teplota `21.5 °C`).
* `text` / `label` – informační popis nebo stav.
* `time` / `date` – časový nebo datový údaj.
* `btn` – tlačítko vyvolávající akci přes `runMethod.json`.
* `fve` – zobrazení stavu a přebytků fotovoltaiky.

---

## 7. Struktura navigace a stránek nové aplikace

Doporučené rozdělení stránek v routeru:

* **`/` (Dashboard / Hlavní stránka):**
  * Přehled aktivních okruhů, TUV, venkovní teploty a rychlé ovládání požadovaných teplot.
* **`/units` (Jednotky tepelného čerpadla):**
  * Podrobný stav jednotlivých TČ v kaskádě (TČ 1–4), diagramy a aktuální výkon.
* **`/error` (Diagnostika a alarmy):**
  * Tabulka aktivních poruch, historie chybových kódů, možnost kvitace chyb.
* **`/:id` (Detail vybrané komponenty):**
  * Plná parametrizace dané komponenty dle jejího typu a konfiguračních bloků.
* **`/history/:id` (Grafy a záznamy):**
  * Vykreslení časových řad teplot, výkonů a spínání z `xcc.component.Logger`.
* **`/config` (Systémová správa – pouze pro adminy):**
  * Správa modulů, přidávání a odebírání komponent (`addFunction.json`, `removeFunction.json`).
  * Záloha a obnova konfigurací (`saveConfig.json`, `loadConfig.json`).
  * `/config/states` – surový výpis vnitřních proměnných PLC.

---

## 8. Doporučený návrh moderní implementace

### Architektura projektu:
```text
src/
├── api/
│   ├── client.ts         # Axios/fetch klient s base URL http://192.168.0.122
│   ├── auth.ts           # login, logout, kontrola cookies (logged, jpar)
│   ├── components.ts     # functions.json, add/removeFunction
│   ├── data.ts           # getData.json, saveData.json, mask builder
│   ├── methods.ts        # runMethod.json, add/removeFromArray
│   └── modules.ts        # modules.json, types.json
├── hooks/
│   ├── useAuth.ts        # React kontext pro autentizaci a admin roli
│   ├── usePolling.ts     # TanStack Query interval 2s pro vyčítání stavu
│   └── useSaveQueue.ts   # Fronta změn s debounce a optimistickým updatem
├── types/
│   ├── api.ts            # Schémata API požadavků a odpovědí
│   ├── components.ts     # Rozhraní pro TopnyOkruh, Tuv, HeatPump atd.
│   └── widgets.ts        # Typy pro switch, choice, number atd.
├── components/
│   ├── widgets/          # UI komponenty (SwitchWidget, NumberWidget, ...)
│   ├── layout/           # Hlavní navigace, stavová lišta, záhlaví
│   └── diagnostics/      # Tabulka chyb a alarmů
└── pages/
    ├── DashboardPage.tsx
    ├── UnitsPage.tsx
    ├── ErrorPage.tsx
    ├── ComponentDetailPage.tsx
    └── ConfigPage.tsx
```

### Ukázka TypeScript klienta pro synchronizaci:
```typescript
// src/api/data.ts
export interface SaveChange {
  id: string | number;
  propPath: string[];
  value: any;
}

export async function fetchComponentData(mask: Record<string, any>) {
  const response = await fetch('/getData.json?status', {
    method: 'POST',
    headers: {
      'Accept': 'application/json',
      'Content-Type': 'application/json; charset=utf-8'
    },
    body: JSON.stringify(mask),
    credentials: 'same-origin'
  });
  if (!response.ok) throw new Error(`HTTP error ${response.status}`);
  return response.json();
}

export async function saveComponentData(changes: SaveChange[]) {
  const response = await fetch('/saveData.json', {
    method: 'POST',
    headers: {
      'Accept': 'application/json',
      'Content-Type': 'application/json; charset=utf-8'
    },
    body: JSON.stringify(changes),
    credentials: 'same-origin'
  });
  if (!response.ok) throw new Error(`Save failed: ${response.status}`);
  return response.json();
}
```

---

## 9. Shrnutí pro implementaci

1. Backend komunikuje výhradně přes **JSON nad HTTP** (22 identifikovaných endpointů).
2. Není potřeba žádný WebSocket – veškerá synchronizace probíhá přes periodický **2s polling `POST /getData.json`** s projekční maskou vlastností.
3. Zápisy probíhají přes **`POST /saveData.json`** s přesnou cestou k vlastnosti (`propPath`).
4. Autentizace je založena na standardních cookies (`logged`, `jpar`), které při lokálním vývoji řeší `vite` proxy směřovaný na `192.168.0.122`.
