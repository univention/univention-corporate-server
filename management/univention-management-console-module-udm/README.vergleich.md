Hallo zusammen,

ich schaffe es nicht, meine inhaltlichen Punkte innerhalb von 10 Minuten im Meeting zu präsentieren oder in das Dokument einzupflegen.
Deshalb würde ich das lieber schriftlich in dieser E-Mail machen.

Ich möchte einmal beide Ansätze zur Implementierung gegenüberstellen, um zu sehen, was die grundlegenden unterschiede sind. Dazu stelle ich beide einmal vor und gehe danach auf die Unterschiede ein:

Daniels Ansatz
==============

# Dazu mal einen groben Überlick darüber, wie ich Daniels Implementierung verstehe und analysiert habe:

* Letztes Jahr wurde eine "Simple" UDM Python Implementierung eingeführt, die als Grundlage für die Implementierung dient.
  * → Ein versionisierter Wrapper um UDM, der mehr Eleganz in die Benutzung von UDM reinbringt, weil ein Programmierer nicht mehr wissen muss, welche Dinge man machen muss, damit man UDM richtig benutzt. Somit entfällt auch einiges an Boilerplate Code.
* Dadurch werden Syntax-Klassen gewrappt, damit z.B. kein base64 encoding mehr benötigt wird (?)
* Dadurch ist es möglich die Properties der Objekte einzuschränken (bzw. man muss jedes mal, wenn es ein neues gibt, dies auch in der API hinzufügen) (?)
* Die Implementierung benutzt das Python-Web-Framework "flask"
* Flask wird über den Python-WSGI Server gunicorn angesprochen (soweit ich sehen kann mit multithreading und multiprocessing)
* Die HTTP-Schnittstelle bietet alle CRUD (create, update, delete)-Operationen über die HTTP Methoden GET, POST, PUT, DELETE an
* Jedes Objekt ist eine einzelne Ressource und hat eine (fast) eindeutige URL
  * z.B: `/udm/users/user/Administrator`, `/udm/container/dc/base`
* Das Datenformat für alle Anfragen und Antworten ist ausschließlich JSON
* Zusätzliche nicht-Standardisierte HTTP header können benutzt werden, um z.B. LDAP-Suchbasis, Scope, etc. beim Suchen einzuschränken
* Der Einstiegspunkt ist eine HTML Seite, die ein JSON-Swagger-Schema zum Download anbietet
* Mittels JSON-Swagger werden alle möglichen Operationen und Ressourcen/Objekte in ein Schema geladen und daraus kann man sich automatisch ein Client in fast jeder Programmiersprache erstellen
* Jede Anfrage macht einen LDAP-bind

# Die Vision
* Die Schnittstelle kann in allen Programmiersprachen ziemlich einfach genutzt werden
* UDM-Code wird nicht mehr für die Client-Library (z.B. UDM-CLI) benötigt
* Das Backend (LDAP) ist austauschbar

# Was momentan noch nicht in der Implementierung enthalten ist:

* Passwort hashes werden nicht entfernt
* Keine Fehlerbehandlung, ziemlich alles läuft auf ein HTTP 500 Internal Server Error hinaus
* Jedes Objekt bietet alle Operationen (Anlegen, Löschen, Bearbeiten) an, obwohl nicht jedes Objekt in UDM diese Operationen unterstützt. Keine Möglichkeit für dynamisches Einschränken.
* Die "default" UDM Option wird nicht herausgefiltert
* Es gibt keine Übersetzung, alles ist in der System-locale (aber es gibt auch fast nichts zu übersetzen, da der Fokus eigentlich nur auf Objekt-Manipulation liegt)
* Nach einem Server-Password-Change werden die LDAP Verbindungen nicht neu aufgebaut. Dann funktionieren keine weiteren Operationen und alles läuft auf ein 500 Internal Server Error hinaus.
* Keine Validierung der Eingabedaten (z.B. ungültige DN's, kaputte Suchfilter, durch Substring-Suchen kann man Passwörter herausfinden)
* Kein intelligentes Nachladen von Extended Attributes. Der Server Prozess läuft in gunicorn gesteuerten Prozessen.
* Keine Einschränkung von Suchfiltern, komplexe Filter können DoS verursachen.
* Verschieben von Objekten fehlt bisher
* Löschen von Objekten hat kein "remove referring objects"

Das kann man alles noch nachpflegen, manche Sachen sind ggf aufwändiger (z.B. Error handling, Sprache) andere eher weniger.

# Außerdem wirken ein paar Dinge auf mich inkonsistent:

* LDAP-Daten und HTTP-API-URL's werden viel vermischt genutzt:
  * die Gruppen eines Benutzers müssen als URL angegben werden, nicht als DN
  * Die Position eines Objekts muss als DN angeben werden, nicht als URL
  * Such-Basis wird als HTTP-Header mit der DN genutzt
* Die URI enthält die ID, nicht die DN eines Objekts und ist daher *nicht* eindeutig
  * z.B. /udm/containers/cn/dns erzeugt einen Crash, weil es 2 Container im LDAP an unterschiedlichen Positionen gibt, die "dns" heißen
  * Löschen von einem Objekt an Stelle X und Wiederanlegen eines Objekts mit selben identifier/name an einer anderen Stelle Y hat dieselbe URL
  * Um das Verhalten einzugrenzen müssen HTTP Header "base: cn=dhcp,dc=base" angegeben werden. Erklär das mal einem HTTP-Cache!
* Das Response-Payload beinhaltet mehrmals/redundant eine "ID", die eigentlich nicht nötig ist? (URL sollte reichen bzw. das entsprechende Feld z.B. "username": foo, der eh im body enthalten ist)

# Swagger:

* Die Performance von Swagger ist momentan ziemlich langsam (und ich weiß nicht genau woran das liegt):

Das laden des Swagger-Schema dauert 15,49 Sekunden, ohne, dass überhaupt irgendwas passiert ist (z.B. Authentifikation, Benutzer anlegen)

```
2 Kerne, 2 GB RAM
$ time python client.py
Connecting to 'http://10.200.3.2:80/udm/swagger.json'.
Time to retrieve swagger schema: 9.57s.
Time to create client from swagger schema: 4.37s.
real    0m15,490s
user    0m4,880s
sys     0m0,732s
```

* Das Swagger-Schema darf *momentan* von HTTP-Caches zwischengespeichert werden, somit sind Clients hinter einem Proxy-Cache bei Änderungen kaputt
* Ein Swagger-Schema ist im Prozess-RAM enthalten. Wenn in der Zwischenzeit neue Extended Attributes oder neue Module erstellt werden, sind diese nicht enthalten:
  * → Problematisch z.B. bei Joinscriptausführung während Paketupdates
  * → Wenn sich Swagger nicht beschleunigt braucht man irgendein Caching, wodurch das obige zum Problem wird
* Weiteres bzgl. Swagger weiter unten

Florians Ansatz
===============
Wir haben durch das UMC-Modul für UDM bereits alle Funktionalitäten implementiert, die benötigt werden um einen Dienst/Schnittstelle anzubieten.
Die Funktionalitäten, die UDM hat gehen weit über die einfachen CRUD-Operationen hinaus.
Die Implementierung ist seit Jahren stabil, dadurch, dass sie in UMC getestet ist.
Aber:

# Problematik im aktuellen UDM-UMC-Modul
* Das Format des HTTP-Request & Response ist weder HTTP-Konform noch RESTful:
  * Alle Anfragen sind ein HTTP `POST` request
  * gerichtet an eine fixe URL unabhängig von den Ressourcen/Objekten (z.B. `/univention/command/udm/put`)
  * mit einem JSON-Body `{"options": {"$dn$: ..., …}, "flavor": "users/user"}` → `{"result": {}}` und somit ziemlich "hässlich".
  * sehr viel komplexe Logik im Javascript, die eigentlich ins backend gehört
  * uvm.

Ich habe über Jahre hinweg versucht, dies zu verbessern und in eine technisch bessere Richtung zu lenken. z.B. habe ich:
* die Möglichkeit geschaffen HTTP-Header im UMC-Server zu benutzen
* sowohl das Error handling überarbeitet als auch die Fehler-Status codes an gültiges HTTP angepasst.
* einige HTTP Sicherheitsmechanismen in den UMC-Server eingebaut
* generische Abläufe in den UDM-Core verschoben

Wie löse ich diese Probleme?:

# Florians Implementierung der UDM-Schnittstelle
* UDM wird in `univention.management.console.modules.udm.udm_ldap` gewrappt um die generischen Funktionalitäten von UDM einfacher zu benutzen. Genauso wie das die neue Simple UDM API tut.
* Das UDM-UMC-Modul nutzt diesen Wrapper in `univention.management.console.modules.udm.__init__` und baut ein hässliches Format (siehe oben) drumherum.
* Der REST-Dienst von mir nutzt auch diesen Wrapper (parallel zum UMC Modul) und baut ein verlässliches Format.
* Als Basis für den HTTP-Server dient das [Python Tornado](https://github.com/tornadoweb/tornado) Framework.
  * Ein dauerhaft laufender TCP-Dienst (nicht WSGI)
* asynchrone Verarbeitung von Anfragen (Threads und Prozesse sind aber auch möglich und werden genutzt)
  * somit ähnlich zur Philosophie von `python-notifier` aber in gut und modern

## CRUD-Operationen in der Schnittstelle
* Jedes UDM Objekt ist über eine eindeutige URI identifiziert
  * `/udm/$object-type/$dn` → `/udm/users/user/uid=Username,cn=users,dc=dev,dc=local` / `/udm/users/user/uid%3DUsername%2Ccn%3Dusers%2Cdc%3Ddev%2Cdc%3Dlocal`
* Die korrekten HTTP Methoden GET / PUT / POST / PATCH / DELETE werden benutzt
* Alle Daten sind in JSON serialisiert (die Struktur muss noch verbessert werden, es enthält momentan einige unnötige Dinge aus dem UMC-Modul)
* Suchparameter (z.B. basis, scope, filter, fields, etc.) ist über den Query-String möglich (anstatt ǘber nicht-standardisierte HTTP header)
* Beispiele sind [hier](README.http_requests.md) enthalten
* Das ist vom Funktionsumfang quasi alles ziemlich identisch zu dem, was die Schnittstelle von Daniel bereitstellt.
  * Das JSON-Format könnte man mit wenig Aufwand 1-zu-1 an Daniels Implementierung anpassen

## Weiteres
* TODO: kommt später… falls notwendig…

Unterschiede zwischen den Implementationen
==========================================

# Wrapper

In der Diskussion über die verwendeten Wrapper-Bibliotheken ist ein bisschen etwas vertauscht worden. Zitat:

```
Die Implementierung von Daniel basiert direkt auf der vereinfachten UDM API und exponiert damit direkt die Datenstrukturen und Funktionen von UDM.
Florians implementierung basiert auf einer für UMC erstellen Bibliothek als “wrapper” für UDM, die weitere Funktionen ergänzt und Datenstrukturen abstrahiert.
```

Das Ganze ist aber eher umgekehrt.

Die UDM-Wrapper Funktionen sind wesentlich näher an den Datenstrukturen und Funktionen von UDM sowie UDM-CLI. Leider wurde in der Vergangenheit viel Verhalten von UDM doppelt Implementiert in der CLI sowie im UMC-Modul. Ich habe bereits einige Dinge davon generisch in den Kern von UDM verschoben.

Die Simple-UDM-API ist auch ein Wrapper, der die Datenstrukturen von UDM-Core verändert. z.B. werden Syntax-Klassen gewrappt um Listen in Dicts umzuwandeln oder 0/1 Strings in Booleans.

Das ist sicherlich an einigen Stellen sinnvoll, aber eigentlich müssten wir solche Strukturänderungen direkt in UDM machen.

Der UDM-UMC-Wrapper akzeptiert übrigens True/False Werte anstatt 0/1-Strings (da die Syntax-Klassen das sowieso schon können).

# TODO: weitere Unterschiede auflisten
* Die URL ist eindeutig, daher beinhaltet sie die gesamte DN anstatt nur z.B. den Benutzername.
* Orignale Syntax-Klassen / Encoding-Wrapper
* Passwörter werden aus den Responses gefiltert


RESTful
========
Ein Thema, was wir noch nicht besprochen haben ist, was eine REST-Schnittstelle ist und ob wir eine haben wollen.

# Was ist RESTful

Der Begriff `RESTful` ist leider seit ewigen Zeit nicht verstanden worden, mittlerweile aber ein Mode-Begriff für jegliche auf HTTP basierende Schnittstellen, die in keinster Weise die Eigenschaften einer REST-API aufweisen.

In ein paar Sätzen zu erklären, was `Representational State Transfer` überhaupt bedeutet und welche Vorteile dadurch entstehen, kann ich hier nicht machen.

Ich habe dazu mal einen Uttuusch gemacht, das Video gibt es irgendwo in /home/groups / owncloud /etc.

Die Definition davon, was REST ist liegt allerdings in der Authorität von dem Begründer Roy T. Fielding.

Was irgendwelche Leute an Meinungen auf Stackoverflow + Wikipedia (+ Richardson Maturity Model) haben ist leider schlichtweg falsch und unvollständig und spiegelt in keinster Weise, die Idee hinter REST dar.

Roy T. Fielding arbeitet als Teil der HTTP Working Group des IETF, die für alle RFC-Standards verantwortlich sind (also auch für HTTP).

Im Internet gibt es (nicht nur von Fielding selbst) unendlich viele Blog-Posts von Software-Architekten, die sich darüber aufregen, dass der Begriff immer falsch verwendet wird (und auch z.B. Verbesserungen am Wikipedia Eintrag von irgendwelchen Leuten wieder rückgängig gemacht werden).

Aber das ganze ist keine Frage der Religion sondern eigentlich gut beschrieben in einem Unterkapitel seiner Dissertation von Roy T. Fielding und durch einige Beiträge von ihm noch erweitert:

* [REST Architekturstil](https://www.ics.uci.edu/~fielding/pubs/dissertation/rest_arch_style.htm)
* [REST API's MUST be hypertext driven](https://roy.gbiv.com/untangled/2008/rest-apis-must-be-hypertext-driven)
* [Spezialization](https://roy.gbiv.com/untangled/2008/specialization)
* [No REST in CMIS](https://roy.gbiv.com/untangled/2008/no-rest-in-cmis)
* ...

Eine REST-API muss ganz genaue Eigenschaten besitzen und Bedingungen befolgen, bis sie RESTful genannt werden kann.
Davon werde ich ein paar für uns relevante Punkte beschreiben, die sich für uns vorteilhaft oder nachteilig auswirken.

# REST Vor- und Nachteile für uns

## Anforderung: Authentifizierung mit einem Token

REST hat die Bedingung, dass Kommunikation zustandslos sein muss.

Das Bedeutet, dass in jeder HTTP-Nachricht alle Informationen enthalten sein müssen, um die Nachricht ohne weiteren Kontext zu verstehen.

Dadurch ist es nicht notwendig, auf Serverseite einen Zustand zwischen zwei Anfragen zu speichern.

I.e. es darf keine (nach außen sichtbare) Session und keine Cookies geben.

Wenn wir jetzt im Anforderungsdokument darüber nachdenken, eine Session basierte Authentifizierung per Token+Cookie zu ermöglichen, kann man z.B. keine Lastverteilung mehr machen (z.B. auf DC Backups).

Der Server Prozess darf dann auch nicht zwischendurch neu gestartet werden oder abstürzen (bei in memory-sessions).

Die Problemlösung für REST ist daher:
* HTTP Basic Authentifizierung zu benutzen

Auch, dass dadurch bei jeden Request ein LDAP-Bind gemacht werden muss ist ein Mythos:
* Die Anfragen beinhalten immer Username+Password, was intern für einen LDAP-Connection cache verwendet werden kann und auch schon so in UMC gemacht wird.
* Wird der {UMC,LDAP}-Server neugestartet kann einfach der Cache verworfen werden und ein neues LDAP-Bind gemacht werden.

### SAML
SAML ist auch in keinster Weise RESTful, da Cookies benötigt werden.
Unser SAML-Service Provider ist im UMC-Webserver implementiert.

Wenn es eine Anforderung ist, dass die API SAML-Authentifikation unterstützen soll, muss entweder der ganze Netzwerkverkehr über den UMC-Wevserver laufen oder eine eigener Service Provider für den REST-Dienst muss implementiert werden.

Ich würde es begrüßen, wenn der UMC-Webserver die übergeordnete Instanz für den REST-Dienst ist:
* Solange wir als Ziel haben UMC-Webserver und UMC-Server zu vereinen und mit Tornado/etc. zu betreiben
* Ermöglicht auch, dass wir unser UMC-ACL Handling erweitern und für den Dienst benutzen (was ja die Anforderung `Delegative Administration` ist).

## UDM ist dynamisch erweiterbar

Aus REST Sichtweise sind Inhalte dynamisch und eine Schnittstelle muss skalieren und die Möglichkeit haben, sich entwicklen zu können.
* Ein Schema kann existieren, aber dieses ist nicht fix.
* Neue Attribute/Module/etc. kommen hinzu, andere werden gelöscht.
  * → Ein Client sollte damit kein Problem haben. Alles was er nicht kennt ignoriert er einfach.
* Wenn es dann wirklich zu Breaking Changes kommt und kommen muss:
  * z.B. Im User-Agent die UCS-Versionsnummer des Client mitsenden. Für Altlast-Clients könnte man das alte Verhalten emulieren.
* NO-GOs sind sowas wie /api/v2/ in der URL oder querystring oder gar im Mimetype.

→ Durch dieses RESTful Verhalten entfällt komplett die Versionisierung der API.

Zitat aus dem Anforderungsdokument: `Die API hat eine stabile API - Veränderungen nur über Versionierung innerhalb der API`
In der Implementierung von Daniel ist aber vorgesehen, dass man über URL's versionisieren kann.
Aber wie soll das in der Praxis funktionieren?

UDM kann durch extended attributes dynamisch erweitert werden. Dadurch wird es niemals möglich sein, ein festes Schema zu haben, was unsere Dienste abbildet.
Swagger ist aber genau für so ein festes Schema gedacht.

Das Swagger-Schema wird momentan aber automatisch generiert und verändert sich bei jedem Extended Attribute, etc.
z.B. denkbar ist ja auch ein Default-Wert eines extended attributes verändert sich.
Für die Anforderung müsste sich also bei jeder Veränderung die Versionsnummer erhöhen.
Mit der Implementierung von Daniel sind also die Anforderung nicht gegeben.

Code-Technisch wäre es ziemlich schwierig für Anfragen zur alten API Version /api/v1/ das alte Verhalten zu liefern!
Die Alternative dazu wäre die alte Version abzuschalten und alle alten Clients nicht mehr zu supporten?
Wo ist da die Skalierbarkeit und Erweiterbarkeit?

Wenn wir Swagger benutzen müssen wir das Schema jedes mal dynamisch generieren oder einen sehr intelligenten Cache-Mechanismus implementieren.
* Das wäre entweder fehleranfällig (race conditions) oder performancekritisch (wie oben bereits beschrieben).

## Uniform Interface
Als nächstes komme ich auf die richtige Art und Weise einer Versionisierung in REST.

Aus REST-Sicht versionisiert man das Interface und nicht den Inhalt (Properties, Objekttypen, etc.), der sich dynmaisch jederzeit verändern können sollte.
Oder anders ausgedrückt: REST benutzt das Protokoll als Schnittstelle und nicht die Implementierung (und ist dadurch skalierbar & wartbar).
Das Interface ist ein von allen Clients generisch bekanntes hypermedia Format (z.B. HTML).

Ein Server sollte jederzeit die Möglichkeit haben, z.B. seine URL-Struktur zu ändern.
Ein Client kennt idealerweise nur eine URL für seinen Einstiegspunkt und hat von dort die Möglichkeit, alle weiteren Zustandsveränderungen zu machen. (Das ist der Grund, warum es Representational State Transfer heißt).

In der Praxis sollte das dann so aussehen, dass es in der Einstiegsurl und allen folgenden URL's HTML `<link>` und andere Elemente oder der `Link` HTTP-Header enthalten ist.
Jeder Link hat eine relation (Bezierhungstyp zu dem aktuellen Dokument).

Beziehungstypen werden von der IANA [hier](https://www.iana.org/assignments/link-relations/link-relations.xhtml) definiert. Zusätzlich kann man eigene erfinden.

Einige Beispiele dafür:
Wenn ich mir eine Liste von 100 Objekten verteilt auf 2 Seiten anzeigen lasse kann das auf verschieden Weise implementiert werden (`udm/users/user/?page=1&num=50` oder `udm/users/user/page/1`).
Die Erste Seite könnte also nun einen Link zur zweiten Seite beinhalten: `<link rel="next" href="/udm/users/user/?page=1&num=50" type="application/json"/>`.
Wenn der Client "dumm" ist und keine Logik benötigt braucht er lediglich zu wissen, dass er um zur zweiten Seite zu gelangen einen Link mit dem Beziehungstyp `next` sucht.
Die URL ist also eine dynamische Entscheidung des Servers und kann jederzeit zur Laufzeit verändert werden. Das setzt voraus, dass der Client also keine Kenntnisse von URL's hat.

Weitere Beispiele dafür wären z.B. das prüfen, ob es eine Relation "add"/"add-form" gibt, um zu prüfen, ob ein Objekt angelegt werden kann, oder "edit"/"edit-form". Oder "search"/"search-form" zum Suchen.
Denkbar ist auch, dass man eigene Beziehungstypen selber definiert. z.B. habe ich das in dem Prototyp gemacht, um dem Client die Möglichkeit zu geben allerhand Metadaten abzufragen:
* Objekttypen, UDM-Optionen, Layout, Default-Werte, Mögliche Werte, Property-Beschreibungen, Hilfe-Texte, Templates, Default-Container, Policy-Typen, Report-Typen, Default-Suchmuster, nächste Freie IP-Adresse

<link rel="/udm/relations/layout/" href="/udm/users/user/layout"/>

Ich könnte damit also theoretisch eine URL verändern in `/udm/users/user/layout/uid=Administrator,cn=users,dc=base` wenn das Layout plötzlich aus irgendeinem Grund von dem gewählten Benutzer abhängt.
Ein Client der dieses Interface benutzt hätte keine Probleme. Ein Client, der hartkodierte URL's verwendet hingegen schon.

Auch hier könnte bei breaking changes ein neuer Beziehungstyp (z.B. `/udm/relations/extended-layout/`) hinzugefügt werden.

### Warum wäre so etwas sinnvoll und wünschenswert?

Diese Form ist natürlich nicht so eine pragmatische schnelle Lösung, wie es eine automatische-Swagger-Client-generierung-Lösung ist!

Die überwiegenden HTTP-Client-Libs stellen auch nicht automatisch Link-Relationen aus HTTP Header oder HTML-Body zur Verfügung.
Wirklich schwierig so etwas zu implementieren ist es aber auch nicht. Ein Beispiel habe ich in [client.py als Nachbau von UDM-CLI](client.py) gestartet.
Mit generischen Bibliotheken könnte man das wesentlich verbessern. Der Trend in der Zukunft wird hoffentlich auch zu diesem Stil tendieren.

Der Grund, warum ich so etwas haben möchte ist die Reduzierung von Logik in unserem Javascript Frontend.
Die Komplexität und Duplizierung der darin enthaltenen Logik ist nicht schön und nicht wünschenswert.

Diese Form des Interface ist mehr eine Erweiterung der Möglichkeiten als ein Ausschließen von Funktionalitäten!:
* die JSON-Schnittstelle zum Anlegen/Bearbeiten/Löschen/etc. von Objekten sieht ja quasi gleich aus, wie die Swagger-Variante (gleiche HTTP-Methoden, JSON-Datenformat, URL's)
* Niemand würde Clients dazu zwingen, HTML zu parsen oder die Link-Header benutzen (außer die Schnittstellen-Definition)
* Clients könnten hartkodierte Formate, URL's etc. verwenden, ist aber nicht empfohlen, da dynamische Änderungen das ggf. kaputt machen könnten
* Wenn wir definieren, dass unsere Schnittstelle stabil sein soll, können wir natürlich per Coding-Policy Änderungen zwingen Rückwärtskompatibel zu bleiben

→ Das ist ja sowieso policy und wünschenswert
→ App Anbieter wären nicht zu technisch korrektem Verhalten gezwungen
→ UMC kann vereinfacht werden
→ ggf. ist es Möglich Swagger oder ähnliche Tools auch zusätzlich zu implementieren

Für eine UDM-CLI müsste man schauen, ob das sinnvoll wäre.

## Caching
REST erfordert, dass alle Ressourcen implizit oder explizit als Cache/Nicht-Cachebar markiert werden.

## Conditional Requests
HTTP bietet die Möglichkeit, Anfragen an Bedingungen zu knüpfen. Z.b. eine Ressource nur zu verändern, wenn sie noch der aktuellen Repräsentation entspricht. Das ist notwendig um Race-Conditions zu vermeiden.

## Progress State
Lang laufende Operationen sollten asnychron über HTTP mittels HTTP 201 Accepted, Location und Retry-Later und einem Progress-Interface implementiert werden.
HTTP Verbindungen sind dazu desinged, so schnell wie möglich wieder geschlossen zu werden.

## Weitere REST-Best-Practices
* https://www.infoq.com/articles/webber-rest-workflow

# REST und Swagger
Um mir ein bisschen Schreibarbeit zu ersparen habe ich auch einige Blog-Einträge über die Nachteile von Swagger und das nicht-RESTfule von Swagger herausgesucht:

Ich bitte euch folgende Blog-Einträge vollständig zu lesen:
* [Swagger ain't REST. Is that okay?](https://www.howarddierking.com/2016/10/07/swagger-ain-t-rest-is-that-ok/)
* [Swagger is not WSDL for REST, it's much less useful than that](https://www.ben-morris.com/swagger-is-not-wsdl-for-rest-its-much-less-useful-than-that/)
* [The Problems with Swagger](https://www.novatec-gmbh.de/en/the-problems-with-swagger/)
* ...
Swagger ist nicht RESTful sondern JSON-RPC over HTTP / WSDL.
Es ist natürlich etwas besser und transparenter, da mehr Elemente aus HTTP benutzt werden als andere RPC-Stile (SOAP).
Auch wenn OpenAPI v3 Links einführt, wird das noch nicht RESTful sein. OpenAPI möchte lieber an einem pragmatischen Ansatz arbeiten um die alte OpenAPI-Struktur beibehalten zu können.

# Konsequenz
Meine Fragestellung lautet dann natürlich:
* Brauchen wir eine REST-API oder eher eine JSON-RPC HTTP-API?
* Ist es eine Anforderung, dass man sich automatisch Clients in allen Programmiersprachen bauen kann?
* Ist Swagger dsa richtige Tool dafür?
  * → In einem der Blogeinträge wird als bessere Alternative [GRPC](https://grpc.io/) erwähnt.

# Persönliches
Ich beschäftige mich seit 2011/2012, als der Student Marcel für uns den ersten Prototyp von einem RESTful UMC-Server implementiert hat, mit dem Thema REST (und mit HTTP noch länger).

Seitdem habe ich alle RFC's, die mit HTTP zu tun haben gelesen und dafür eine generische HTTP Bibliothek geschrieben (https://github.com/spaceone/httoop/).
Ich kenne also jedes byte aus HTTP.
Zusätzlich habe ich ein asynchrones event basiertes REST-Framework für Python entwickelt (https://github.com/spaceone/circuits.http).

Mir liegt das Thema emotional am Herzen, wie es sicherlich einigen Entwicklern und IETF's auch tut.

Daher bin ich dagegen, dass wir unsere Schnittstelle RESTful nennen, wenn sie das nicht ist. Von mir aus können wir von JSON-HTTP-API, UDM-JSON-Schnittstelle oder sonstiges sprechen.

Architektur
===========
Unabhängig vom Thema REST oder RPC gibt es weitere Architektur-Entscheidungen, die wichtig sind und bedacht werden müssen.
In progress…

# WSGI: Ja oder Nein?
Vorteile:
Nachteile:
* wir haben keinen laufenden Prozess mehr und können somit kein credentials caching benutzen

## oder lieber ein dauerhaft laufender Dienst?
Vorteile:
Nachteile:

## oder ein Prozess in einem übergeordneten Dienst (so wie UMC das macht)
Vorteile:
* SAML einfacher
* generisches ACL-Handling möglich
* Ressourcensparender
Nachteile:

# Authentifizierung
* reines LDAP bind prüft keine deaktivieruns/locked/password-expired status
* PAM ist sicherer
