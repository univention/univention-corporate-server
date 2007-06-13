Lokale Cache Authentifizierung
******************************

Aufgabe:
==========

  Nicht jeder Client hat eine permanente Netzwerkverbindung zu einem
  Domaincontroller bzw. zu dessen Benutzerdatenbank. Da aber auch ohne
  Netzwerkverbindung zum Domaincontroller Master weiterhin eine Anmeldung
  bestimmter Benutzer an diesem Client moeglich sein muss, wird ein lokaler
  Cache bereits angemeldeter Benutzer benoetigt.
  Dieser lokale Cache beinhaltet eine definierbare Anzahl von Benutzer und die
  dazugehoerigen Gruppen.
  Bei der Anmeldung eines Benutzer wird zunachst ueberprueft, ob eine
  Verbindung zum Domaincontroller Master besteht. Falls diese Verbindung
  besteht, wird die Authentifizierung gegen die Benutzerdatenbank des
  Domaincontroller Master durchgefuehrt und die Daten des Benutzers in den
  lokalen Cache eingepflegt.  Besteht keine Verbindung zum Domaincontroller
  Master, so wird gegen den lokalen Cache authentifiziert. 

  Hierzu sind zwei Module zu implementieren:
    - ein PAM Modul fuer die Authentifizierung
  	  Bei erfolgreicher Authentifizierung gegen den Domaincontroller Master
	  wird der lokale Cache aktualisiert
    - ein NSS Modul fuer die Namensaufloesung, alle NSS Funktionen muessen
	  implementiert werden
  	  Stichwort "getent passwd; getent group; ..."

  Behandelte Faelle:
   - es besteht eine Verbindung zum Domaincontroller Master
      - der Benutzer ist im lokalen Cache, aber nicht in der Benutzerdatenbank
	des Domaincontroller Master vorhanden
          * der Benutzer wird aus dem lokalen Cache geloescht
      - der Benutzer ist nicht im lokalen Cache, aber in der Benutzerdatenbank
	des Domaincontroller Master vorhanden
          * der Benutzer wird in den lokalen Cache eingeplegt
      - der Benzter ist im lokalen Cache und in der Benutzerdatenbank des
	Domaincontroller Master vorhanden
          * der lokale Cache wird aktualisiert und der Benutzer rutscht in der
            Rangliste der Benutzer nach oben
      - der Benutzer ist nicht im lokalen Cache und nicht in der
	Benutzerdatenbank des Domaincontroller Master
          * die Anmeldung ist nicht erfolgreich
   - es besteht keine Verbindung zum Domaincontroller Master
      - der Benutzer ist im lokalen Cache vorhanden
          * die Anmeldung ist erfolgreich, wahrscheinlich keine Aenderung am
            lokalen Cache, evtl. rutsch der Benutzer im Cache nach oben.
      - der Benutzer ist nicht im lokalen Cache viorhanden
          * die Anmeldung ist nicht erfolgreich, keine Aenderung am lokalen
            Cache


  Dateien:
      /etc/univention/passwdcache/passwd
          Cache Passwd Datei, analog zur Datei /etc/passwd
      /etc/univention/passwdcache/shadow
          Cache Shadow Datei, analog zur Datei /etc/shadow
      /etc/univention/passwdcache/groups
          Cache Groups Datei, analog zur Datei /etc/groups
      /var/log/univention/passwdcache/passwd-cache.log
          Log Datei, hierzu kann univention-debug verwendet werden
      /lib/security/pam_passwdcache.so
          Benoetigtes PAM Modul
      /lib/nss_passwdcache.so
          Benoetigtes NSS Modul

  Einige Anregungen fuer die Implementierung koennen im winbind Code des Samba
  Projektes angeschaut werden, allerdings muss die Lizenz von Samba beachtet
  werden.  Zusaetzlich existiert im cvs ein PAM Modul, pam_runasroot.

  Anmerkung: Es wurde nur von Domaincontrolle r Master gesprochen, es kann aber
  natuerlich auch ein Domaincontroller Slave/Backup verwendet werden.


  Datei: packages/univention/univention-passwd-cache/README.txt


Ergebnis:
==========

  Im Debian-Source univention-passwd-cache sind
  die Packages nss-passwdcache und pam-passwdcache enthalten.
  Diese können mit dpkg installiert werden.
  Die Pakete werden aber nicht konfiguriert.
  
  NSS-Modul:
  ----------
  Das NSS-Modul ist für den Nameserverswitch der glibc. 
  Dieses Modul dient der Namensauflösung für passwd, shadow und group 
  aus den Datenbanken
  /etc/univention/passwdcache/passwd
  /etc/univention/passwdcache/shadow
  /etc/univention/passwdcache/group

  Diese Textdateien haben die gleiche Struktur wie /etc/passwd usw.
  Diese können durch kopieren hergestellt werden.
  Das NSS-Modul greift auf die Dateien nur lesend zu. Wenn keine Dateien
  vorhanden sind, so wird nichts gelesen und kein Fehler verursacht.
  
  Zum Konfigurieren wird die Datei /etc/nsswitch.conf verwendet.
  Siehe dazu auch "man nsswitch.conf".

  Ein Beispiel für /etc/nsswitch.conf ist:
  
  passwd:         compat ldap passwdcache
  group:          compat ldap passwdcache
  shadow:         compat ldap
  hosts:          files dns
  networks:       files

  Der Inhalt des Cache kann zum testen mit
  getent -s passwdcache passwd
  getent -s passwdcache group
  ausgelesen werden.
  Als Gegenprobe kann 
  getent passwd
  oder
  getent -s files passwd
  benutzt werden.
  ("getent -s ldap passwd" verursacht bei mir ein Segmentation fault)


  PAM-Modul:
  ----------
  Das Pluggable Authentication Module dient dem Authentifizieren der Benutzer.
  Das PAM-Modul erstellt automatisch die cache-Dateien und die Pflegt die
  Einträge. Solange eine Autentifizierung über ein anderes PAM-Modul erfolgreich
  ist, werden gültige Benutzer hinzugefügt oder aktualisiert und
  ungültige Benutzer entfernt. Wenn keine anderes PAM-Modul den Benutzer
  autentifizieren kann, wird gegen den Cache geprüft.
  Der Cache wird dann in diesen Fall nicht verändert. 
  
  Das Konfigurieren der PAM-Module ist nicht einfach,
  da die einfache Schreibweise nicht ausreichend ist.
  Siehe dazu auch "man 7 pam".
  Das Modul pam_passwdcache versteht die Argumente debug, insert, delete,
  try_first_pass, use_first_pass und max_user=[0..n].
  Debug schalte ein geringes Logging hinzu.
  Das Ergebnis kann in /var/log/auth verfolgt werden.

  "Insert" teilt dem Modul mit, das eine Verbindung zum Master verfügbar ist,
  und der sich anmeldene Benutzer gültig ist.
  Dieser wird in den Cache hinzugefügt oder aktualisiert.

  "Delete" teilt dem Modul mit, das eine Verbindung zum Master verfügbar ist,
  und der Benutzer aus den Cache entfernt werden soll.

  Ohne "Insert" oder "Delete" wird der Cache nicht verändert.
  Der Cache wird dann aber zum Authentifizieren verwendet.
  
  max_user limitiert die Anzahl der Benutzer im Cache. Wenn weitere Benutzer
  hinzukommen werden automatisch die ältesten entfernt.
  Der neueste Benutzer wird am Ende der Datei eingefügt.
  Am Anfang der Datei ist der älteste Benutzer.

  Ein Beispiel für /etc/pam.d/common-auth ist (Achtung, breite Zeilen):


  auth sufficient                                                                               pam_unix.so debug
  auth [success=ok new_authtok_reqd=ok service_err=2 system_err=2 authinfo_unavail=2 default=1] pam_ldap.so use_first_pass
  auth [success=done new_authtok_reqd=ok ignore=ignore default=bad]                             pam_passwdcache.so debug try_first_pass insert max_user=3
  auth required                                                                                 pam_passwdcache.so debug try_first_pass delete max_user=3
  auth sufficient                                                                               pam_passwdcache.so debug try_first_pass


  Zum Testen einfach an's System anmelden.
  Aber Achtung! Wenn die Konfiguration falsch ist, kommt keiner mehr rein.
  Zur Sicherheit eine offene Verbindung halten.
  
