# maaki
Maaki-projektissa tuotetaan kiinteistökohtaista turvetietoa yhdistämällä avoimia paikkatietoaineistoja.

## Käytetyt aineistot

Maalaji: Maaperä 1:200 000 (maalajit) / Geologian tutkimuskeskus / 2002-2009 / https://hakku.gtk.fi/fi/locations/search?location_id=3

Maannos: Suomen maannostietokanta / Luonnonvarakeskus / 2009 (päivitetty 2014-2016) / Saatu Lukesta kysymällä, verkossa puutteellinen versio / https://ckan.ymparisto.fi/dataset/suomen-maannostietokanta

Corine: Corine maanpeite 2018 / Suomen ympäristökeskus / rasteri / https://www.syke.fi/fi-FI/Avoin_tieto/Paikkatietoaineistot/Ladattavat_paikkatietoaineistot

Kiinteistörekisteri: Datahuoneen metsädatassa hyödynnetty kiinteistörekisterikartta / Alkuperä Maanmittauslaitos / https://asiointi.maanmittauslaitos.fi/karttapaikka/tiedostopalvelu/kiinteistorekisterikartta_vektori

Maakuntajako: Hallinnolliset aluejaot (vektori) / Maanmittauslaitos / 2023 / https://asiointi.maanmittauslaitos.fi/karttapaikka/tiedostopalvelu/hallinnolliset_aluejaot_vektori


## Aineistojen käsittely

Ennen yhdistämistä aineistot on 
1. Vaihdettu koordinaattijärjestelmään ETRS89 / TM35FIN(E,N) (EPSG:3067) lukuunottamatta kiinteistörekisteriä, joka on koordinaattijärjestelmässä EPSG:4326 - WGS 84
2. Korjattu geometrioiltaan

Lisäksi Corine maanpeite 2018 on muunnettu vektorimuotoon ja siihen on rasterimuodosta liitetty LEVEL4 ja sen kuvaus suomeksi.


## Aineistojen yhdistäminen GIS-mallilla

Maaperää, maannosta, maanpeitettä, ja kiinteistötietoja kuvaavat karttatasot yhdistettiin maakunnittain QGIS-ohjelman graafisella mallintajalla rakennetulla algoritmilla (maakiModel.py/maakiModel.png) ja lopputulos tallennettiin sekä paikkatiedon säilyttävässä GeoPackage-muodossa että jatkokäsittelyyn tarvittavana csv-taulukkona. Yhdistämisen välitulokset tallennettiin toistaiseksi GeoPackage-muodossa. 

Maannostietokantaan ei ole määritelty vesistöjä, joten maaperä- ja maannosaineistojen yhdistämiseen oli käytettävä union-algoritmia, joka ottaa sijainniltaan päällekkäisten kuvioiden lisäksi mukaan myös kuviot, jotka kuuluvat vain toiselle tasolle. Maannoksen ja maaperän yhdisteessä vesistöt ovat siis mukana, mutta niiden maannostiedot ovat tyhjät.  Muuten maannos- ja maaperäaineistot ovat kuviorajauksiltaan hyvin samanlaisia, sillä maaperäaineistoa on käytetty maannostietokannan rakentamisen pohjana. Maaperäaineisto on hieman tarkempi, joten esimerkiksi maannostietokannan mukaisesta eloperäisestä histosol-kuviosta osa saattaa olla maaperäaineiston mukaisesti kivennäismaata. 

Aineistojen suuren päällekkäisyyden, mutta rajojen ilmeisen epätarkkuuden vuoksi maannoksen ja maaperäaineiston yhdistelmä sisälsi tuhansittain raja-alueille sijoittuvia kuvioita, jopa nollapinta-aloilla. Aineiston siistimiseksi poistettiin rivit, joita ei pitäisi olla, eli vesistöt, joille on määritelty maannos, maa-alueet, joille ei ole määritelty maannosta, sekä rivit, joilla ei ole pintamaalajia lainkaan. Lisäksi poistettiin kaikki alle neliömetrin suuruiset kuviot, sillä näiden raja-alueiden rivimäärät olivat merkittäviä, mutta pinta-alat merkityksettömiä. 

Maanpeitettä kuvaava Corine-aineisto sekä kiinteistörekisteri voitiin yhdistää ristiinleikkauksella, sillä aineistot kattoivat koko Suomen pinta-alan. Kussakin ristiinleikkausvaiheessa aineistoista säilytettiin vain tarpeellisina pidetyt muuttujat. 

Maaki-mallin lopullisessa tuloksessa on rivi kullekin maaperän ja maannoksen yhdisteen, Corine-maanpeiteaineiston sekä kiinteistörekisterin ristiinleikkauksessa syntyvälle kuviolle. Säilytettyjä muuttujia ovat kiinteistötunnus kiinteistörekisteristä, LEVEL4-maanpeiteluokka Corine-aineistosta, maannosta kuvaava SOIL_BODY maannostietokannasta sekä pintamaalajia vastaava koodi maaperäaineistosta. Lisäksi kullekin kuviolle on laskettu pinta-ala hehtaareina. 





