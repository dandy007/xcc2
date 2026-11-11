# XCC PLC pro Home Assistant

Vlastní integrace pro čtení stavů regulátoru XCC přes jeho HTTP JSON API. Data se obnovují každých 10 sekund.

Integrace vytváří zařízení pro každou komponentu PLC a automaticky vystaví její skalární hodnoty jako senzory. Booleovské hodnoty se zobrazí jako binární senzory. Tato první verze je pouze pro čtení.

## Instalace přes HACS

1. V Home Assistantu otevřete **HACS → Integrace**.
2. V nabídce vpravo nahoře zvolte **Vlastní repozitáře**.
3. Vložte URL GitHub repozitáře, ve kterém je tato integrace publikovaná, a jako kategorii vyberte **Integration**.
4. Vyhledejte **XCC PLC**, nainstalujte ji a restartujte Home Assistant.
5. Otevřete **Nastavení → Zařízení a služby → Přidat integraci**, vyhledejte **XCC PLC** a zadejte adresu regulátoru, uživatelské jméno a heslo.

Ve složce repozitáře musí být `hacs.json` a `custom_components/xcc/`. Repozitář zatím nemá nastavený GitHub remote, proto je potřeba před instalací nahrát tuto větev do GitHub repozitáře a použít jeho URL.

## Lokální instalace pro vývoj

Zkopírujte `custom_components/xcc` do `<config>/custom_components/xcc` a restartujte Home Assistant. Poté přidejte integraci přes obrazovku **Zařízení a služby**.

## Poznámka k API

Integrace se přihlašuje přes `POST /login.json` a načítá data z `GET /functions.json?status&extended`. Výchozí adresa je `http://192.168.0.122`; lze ji změnit v průvodci nastavením.
