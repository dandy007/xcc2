# XCC – technická dokumentace pro Home Assistant

## Účel a rozsah

Tento dokument zachycuje živé rozhraní regulátoru, jeho navigaci a data, která jsou užitečná pro rozšíření vlastní integrace Home Assistantu. Rozhraní bylo procházeno pouze pro čtení. Nebyly použity přepínače, volby, tlačítka pro spuštění/zastavení, aktualizace předpovědi, ukládání ani odhlašování.

Dokument neobsahuje živé hodnoty, identifikátory uživatele, adresu objektu ani obsah session cookie. Některé systémové záložky pro uživatelský kód, změnu hesla a e-mailová upozornění byly identifikovány podle názvů, ale jejich obsah nebyl otevřen ani zaznamenán.

Označení v textu:

- **Pozorováno** – viditelné v živém rozhraní nebo v DevTools během průchodu.
- **Doloženo specifikací/kódem** – popsáno v `TECH_SPEC.md` nebo ve stávající webové aplikaci; nemuselo se objevit v zachyceném síťovém záznamu.
- **Doporučení** – návrh pro budoucí HA entity, nikoli tvrzení o vlastnosti, která byla ověřena na každé instalaci PLC.

## Navigace a stránky

URL stránky používají kořenovou cestu regulátoru. `component_id` je dynamické ID z dat funkce; čísla nejsou stabilní napříč instalacemi.

| Cesta | Obsah |
|---|---|
| `/?tab=0` | Hlavní přehled se souhrnem topení, TUV, bivalence, počasí a indikací stavu systému. |
| `/?tab=1` | Druhá stránka hlavního karuselu; při průchodu měla stejný souhrnný obsah. |
| `/?tab=2` | Stránka „Všechny funkce“ s dlaždicemi komponent. |
| `/<component_id>?tab=<index>` | Detail funkce a její záložky. |
| `/units?tab=0` | Přehled stavů tepelných čerpadel, dosažitelný přes systémovou nabídku „Stavy jednotek“. |
| `/error?tab=0` | Aktuální chyby. |
| `/error?tab=1` | Seznam komponent s dostupnou historií. |
| `/history/<component_id>?tab=<index>` | Historický graf vybrané veličiny komponenty. |

### Hlavní přehled

**Pozorováno:** levý souhrn ukazuje topný okruh, TUV a bivalenci; pravá část počasí a venkovní teplotu; střed obsahuje stav systému. Karusel má tři záložky. Třetí obsahuje dlaždice funkcí. V hlavičce je také odkaz na diagnostiku.

Kliknutí na dlaždici funkce otevře detail komponenty. Ovládací prvky na hlavním přehledu do HA nepřenášet jako zápisy v rámci současného zadání.

### Topný okruh

Detail má pět viditelných záložek:

| Záložka | Zobrazené informace |
|---|---|
| Informace | Stav okruhu; požadovaná a aktuální teplota prostoru; požadovaná teplota topné vody; režim útlumu a vlivu prostoru. |
| Útlum | Režim vypnuto / časový / trvalý a velikost útlumu. |
| Vliv prostoru | Režim bez čidla / termostat / adaptivní, povolené pásmo adaptace, teplotní meze, maximální teplota vody a dočasné vypnutí adaptace. |
| Pokročilé | Venkovní teplotní mez pro vypnutí topení, volba regulace ekvitermní křivkou nebo konstantní hodnotou a korekce prostorového čidla. |
| Ekvitermní křivka | Graf teploty vody podle venkovní teploty, posun křivky a sada bodů křivky. |

**Pozorováno v datovém objektu:** stav obsahuje alespoň `enabled`, `running`, `actTemp`, `reqTemp` a `reqProp`. Rozhraní navíc pracuje s poli jako `requestAir`, `requestWater`, `actualWater` a režimy okruhu; jejich přítomnost závisí na projekci/typu instalace.

### TUV

Viditelné záložky jsou Informace, Sanitace a Pokročilé.

- **Informace:** stav okruhu, aktuální a požadovaná teplota, meze Min./Max., externí ohřev a stav sanitace. Stránka obsahuje i ruční ovládání a tlačítka spustit/zastavit; žádné nebylo použito.
- **Sanitace:** povolení sanitace, cílová teplota, interval ve dnech, čas začátku, informace o posledním spuštění a posledním úspěšném provedení a volba pevného dne. Stránka obsahuje i ovládací tlačítka, která zůstávají mimo rozsah integrace.
- **Pokročilé:** volba ohřevu tepelným čerpadlem nebo externím zdrojem a teplotní mez pro externí ohřev.

**Pozorováno v datovém objektu:** `enabled`, `running`, `actTemp`, `reqTemp`, `reqProp` a `button`.

### Bivalence

Detail obsahuje režim vypnuto / automatický / zapnuto, hysterezi, venkovní teplotní mez pro povolení, čas do sepnutí, hysterezi spínání a minimální dobu běhu. Tyto položky popisují konfiguraci a stav stránky; integrace podle zadání nemá režim měnit.

### Počasí

- Záložka **Info o počasí** zobrazuje časovou tabulku s datem, vlhkostí a teplotou.
- Záložka **Nastavení** zobrazuje nakonfigurovanou lokalitu a stáří dat. Obsahuje tlačítka pro aktualizaci a výběr lokality; nebyla použita.
- Historie počasí má položku externí chyby.

Konkrétní lokalita a časy předpovědi jsou z dokumentace záměrně vynechány.

### Systémový přehled a nastavení

Informační ikona v hlavičce otevře souhrn systému: výkon TČ, stav hlavního vypínače, požadovanou a aktuální teplotu topné vody, venkovní teplotu, HDO, venkovní mez HDO a oběhová čerpadla.

Odkaz **Nastavení** otevřel detail systému s těmito záložkami:

- Vypnutí: hlavní vypínač, ruční globální útlum a datumové zapnutí globálního útlumu.
- Omezení výkonu: globální, časové a teplotní omezení výkonu.
- Uživatelský kód, Změna hesla, Upozornění email: pouze názvy záložek; jejich obsah nebyl otevřen.

Z tohoto systémového detailu je dostupná stránka **Stavy jednotek**.

### Stavy tepelných čerpadel

Stránka `/units?tab=0` zobrazuje jednotky v sekci TČ 1–4. Pro jednotku jsou viditelné:

- horní a dolní otáčky ventilátoru (ot/min),
- teplota kondenzátu, sání, výtlaku a výparníku (°C),
- odebíraný proud (A), výkon (%) a motohodiny.

**Pozorováno v projekci `getData`:** pole v `units[]` zahrnují `pump`, `power`, `tcj`, `mototime`, `fanUp`, `fanLo`, `ts`, `td`, `te` a `curr`. V zachycené odpovědi neměl objekt jednotky vlastní identifikátor. Stabilitu pořadí jednotek je nutné ověřit na více jednotkách; nepovažovat index pole automaticky za trvalé ID.

### Diagnostika a historie

`/error?tab=0` je seznam aktuálních chyb; v právě zobrazeném stavu neměl žádné položky. Záložka `/error?tab=1` obsahuje seznam komponent s tlačítky Historie.

Pozorované typy historických záložek:

| Komponenta | Historické veličiny |
|---|---|
| Bivalence | Čidlo soutoku, čidlo bivalence. |
| Tepelné čerpadlo | Průtok, přetopení, podchlazení, čidlo TCJ, komunikace, čidlo TC, průtokoměr, jednotka. |
| Topný okruh | Čidlo vzduchu, čidlo vody. |
| Počasí | Externí chyba. |
| TUV | Čidlo vody. |

Historické stránky zobrazují rozsah Od/Do a časovou řadu. Hodnoty historie nebyly přepisovány ani ukládány do této dokumentace.

## Síťová komunikace

### Pozorované požadavky v DevTools

| Požadavek | Pozorování |
|---|---|
| `GET /functions.json?status` | Opakované Fetch/XHR požadavky, odpověď `200`, `application/json`. Obsahuje mapu komponent a jejich stavů. |
| `POST /getData.json?status` | Opakované Fetch/XHR požadavky, odpovědi `200`. Používá projekční masku vlastností v těle požadavku. |
| `POST /getData.json?status&extended` | Odpověď `200`; rozšířená projekce obsahuje globální data a pole `units[]`. |

Metoda POST pro `getData.json` odpovídá volání v klientském kódu a API specifikaci. Záznamy DevTools obsahují session cookie; její hodnota se nesmí logovat ani ukládat do HA diagnostiky.

### Datové schéma z pozorovaných odpovědí

Odpověď `/functions.json?status` je mapa položek komponent podle ID. Jedna položka má tvar:

```json
{
  "<component_id>": {
    "id": "<component_id>",
    "name": "<název komponenty>",
    "TYPE": "xcc.component.<Typ>",
    "icon": 0,
    "status": {
      "enabled": true,
      "running": true,
      "actTemp": 0,
      "reqTemp": 0,
      "reqProp": "<název vlastnosti>"
    }
  }
}
```

Konkrétní klíče `status` se liší podle typu komponenty. Vzor je pouze strukturální; uvedené hodnoty nejsou hodnotami PLC.

Rozšířená projekce `/getData.json?status&extended` vrátila objekt globálního systému s klíči:

```text
idGlobal, on, error, time, tempOut, powerAct, tempAct, tempReq,
hdo, hdoIgnore, hdoIgnoreTemp, units[]
```

Objekt každé položky `units[]` obsahoval klíče:

```text
pump, power, tcj, mototime, fanUp, fanLo, ts, td, te, curr
```

Odpověď zahrnovala také metadata vlastníka a adresy objektu. Tato metadata nejsou potřebná pro HA senzory a integrace je nesmí vystavovat jako entity ani zapisovat do logů. `time` je časový údaj; jeho jednotku ověřit před použitím jako HA timestampu.

### Projekční maska

`getData.json` přijímá projekční masku, která vybírá požadované cesty. Pro globální teplotu a data jednotek lze začít touto strukturou:

```json
{
  "<global_id_or_null>": {
    "tempOut": 1,
    "units": [
      {
        "pump": 1,
        "power": 1,
        "tcj": 1,
        "mototime": 1,
        "fanUp": 1,
        "fanLo": 1,
        "ts": 1,
        "td": 1,
        "te": 1,
        "curr": 1
      }
    ]
  }
}
```

Tvar projekce pro další pole by se měl potvrdit v DevTools při čtení příslušné stránky. Vyžádat pouze potřebné vlastnosti a data cachovat podle rozumného intervalu.

## Ověřené a neověřené API

- **Pozorováno:** `/functions.json?status`, `/getData.json?status` a `/getData.json?status&extended`.
- **Doloženo specifikací/kódem:** `POST /getStates.json?all` nebo `?idComp=<component_id>` pro stavy a chyby; specifikaci a příklady masek obsahuje [TECH_SPEC.md](TECH_SPEC.md).
- Během zachyceného průchodu se v DevTools nezobrazil požadavek `getStates.json`; jeho používání webovou stránkou proto zde není potvrzeno.
- Detailní stránky používají stejnou sadu komponent a projekcí; nebyla nalezena potřeba WebSocketu.

## Mapování do HA integrace (verze 0.3.0)

Integrace vedle původních entit z `functions.json` načítá projekci `getData.json?status&extended` a vytváří:

- zařízení **Systém** se senzory venkovní teploty, výkonu TČ, aktuální a požadované teploty topné vody a HDO teplotní meze; systémové `on`, `error`, `hdo` a `hdoIgnore` jsou binární senzory,
- zařízení **Tepelné čerpadlo 1..N** z položek `units[]` se senzory otáček, teplot TCj/TS/TD/TE, proudu, výkonu a surového počítadla motohodin; `pump` je binární senzor.

Komponentní ID zůstávají součástí `unique_id`, takže stávající entity z předchozí verze zachovají své entity ID. Identita jednotlivých jednotek je nyní odvozena od pozice v poli; pokud PLC může pořadí jednotek měnit, je nutné ověřit stabilnější klíč před použitím na vícejednotkovém systému.

`mototime` zůstává jako surová hodnota bez jednotky a bez převodu. Pole `time`, `owner` a `address` se do snapshotu integrace nepřenášejí. Předpověď počasí, historické grafy a konfigurační hodnoty zatím nemají v integraci entity; jejich API projekci je potřeba nejdřív samostatně ověřit.

V souladu se zadáním je integrace pouze pro čtení. Nevolá `saveData.json`, `runMethod.json` ani jiný zápisový/akční endpoint a nevytváří ovládací entity pro změnu hodnot nebo spuštění procesů.

## Zdroje v repozitáři

- [TECH_SPEC.md](TECH_SPEC.md) – reverzně analyzované API a datová projekce.
- [index.html](index.html) – současný klientský kód, který volá `functions.json`, `getData.json` a zapisovací endpointy.
- Živé stránky a DevTools regulátoru – pozorování popsaná výše; žádné živé identifikační údaje nebo provozní hodnoty nejsou součástí dokumentu.
