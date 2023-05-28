#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""UCS installation via VNC"""

from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser
from os.path import dirname, join
from typing import Dict

from installation import VNCInstallation, build_parser, sleep, verbose
from yaml import safe_load


class UCSInstallation(VNCInstallation):

    def load_translation(self, language: str) -> Dict[str, str]:
        name = join(dirname(__file__), "languages.yaml")
        with open(name) as fd:
            return {
                key: values.get(self.args.language, "")
                for key, values in safe_load(fd).items()
            }

    @verbose("MAIN")
    def main(self) -> None:
        self.bootmenu()
        self.installer()
        self.setup()
        self.joinpass_ad()
        self.joinpass()
        self.hostname()
        self.ucsschool()
        import shlex
        import subprocess
        if self.args.password and self.args.ip:
            subprocess.check_call("utils/sshpass -v -p %s ssh  -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null root@%s -C %s" % (shlex.quote(self.args.password), shlex.quote(self.args.ip), shlex.quote("set -x; ucr set repository/online/server='http://apt.knut.univention.de/' repository/online=yes; echo 'deb [trusted=yes] http://omar.knut.univention.de/build2/ ucs_5.1-0/all/' >>/etc/apt/sources.list; echo 'deb [trusted=yes] http://omar.knut.univention.de/build2/ ucs_5.1-0/$(ARCH)/' >>/etc/apt/sources.list; apt-get update; echo erledigt")), shell=True)
        else:
            print('########## error', self.args.password, self.args.ip)

        self.finish()
        if self.args.second_interface:
            # TODO activate 2nd interface for ucs-kvm-create to connect to instance
            # this is done via login and setting interfaces/eth0/type, is there a better way?
            self.configure_kvm_network(self.args.second_interface)

    @verbose("GRUB")
    def bootmenu(self) -> None:
        """
        # Univention Corporate Server Installer
         Start with default settings
         Start with manual network settings
         Advanced options                      >
         Accessible dark contrast installer me >
         Help

        Automatic boot in 60 seconds...
        """
        if self.text_is_visible('Univention Corporate Server Installer', wait=False):
            if self.args.ip:
                self.client.keyPress('down')
            self.type('\n')

    @verbose("INSTALLER")
    def installer(self) -> None:
        # Sprache wählen/Choose language
        """
        # Select a language
        Choose the language to be used for the installed system. The UCS installer only supports English, French
        and German and will use English as fallback. Similar restrictions apply to the parts of the installed
        system which have not yet been localized.

        /Language:/
         ...
         English - English
         French - Français
         German - Deutsch
         ...

        [Screenshot]  [Go Back] [Continue]
        """
        for _ in range(3):
            self.wait_for_text('Select a language', timeout=120)
            self.click_at(250, 250)
            self.type('english_language_name')
            self.type("\n")
            if self.text_is_visible('select_location'):
                break
            else:
                self.click_on('Go Back')

        """
        # Auswahl des Standorts
        Der hier ausgewählte Standort wird verwendet, um die Zeitzone zu setzen und auch, um zum Beispiel
        das System-Gebietsschema (system locale) zu bestimmen. Normalerweise sollte dies das Land sein, in
        dem Sie leben.
        Diese Liste enthält nur eine kleine Auswahl von Standorten, basierend auf der Sprache, die Sie
        ausgewählt haben. Wählen sie »weitere«, falls ihr Standort nicht aufgeführt ist.

        /Land oder Gebiet:/
         Belgien
         Deutschland
         Italien
         Lichtenstein
         Luxemburg
         Schweiz
         Österreich
         weitere
        [Bildschirmfoto]  [Zurück] [Weiter]
        """
        self.click_at(250, 250)
        self.type('location')
        self.type("\n")

        # Access software for a blind person using a braile display
        # Die Sparchsynthesizer-Stimme konfigurieren

        """
        # Tastatur konfigurieren
        /Wählen Sie das Layout der Tastatur aus:/
         ...
         Deutsch
         ...
        [Bildschirmfoto]  [Zurück] [Weiter]
        """
        self.wait_for_text('select_keyboard')
        self.click_at(250, 250)
        self.type('us_keyboard_layout')
        self.type("\n")

        # CD-ROM erkennen und einbinden
        # Debconf-Vorkonfigurationsdatei laden
        # Installer-Komponenten von CD laden

        # Netzwerk-Hardware erkennen

        # Netzwerk einrichten
        if self.args.ip:
            self.network_setup()
            self.click_at(100, 320)

        """
        # Benutzer und Passwörter einrichten
        Sie müssen ein Passwort für »root«, das Systemadministrator-Konto, angeben. Ein bösartiger Benutzer
        oder jemand, der sich nicht auskennt und Root-Rechte besitzt, kann verheerenden Schaden anrichten.
        Deswegen sollte Sie darauf achten, ein Passwort zu wählen, das nicht einfach zu erraten ist. Es sollte
        nicht in einem Wörterbuch vorkommen oder leicht mir Ihnen in Verbindung gebracht werden können.
        Ein gutes Passwort enthält eine Mischung aus Buchstaben, Zahlen und Sonderzeichen und wird in
        regelmäßigen Abständen geändert.
        Das Passwort für den Superuser root muss mindestens 8 Zeichen umfassen.
        Hinweis: Sie werden das Passwort während der Eingabe nicht sehen.
        /Root-Passwort:/
         [...]
         [ ] Passwort im Klartext anzeigen
         Bitte geben Sie das root-Passwort nochmals ein, um sicherzustellen, dass Sie sich nicht vertippt
         haben.
        /Bitte geben Sie das Passwort zur Bestätigung nochmals ein:/
         [...]
         [ ] Passwort im Klartext anzeigen

        [Bildschirmfoto]  [Zurück] [Weiter]
        """
        self.wait_for_text('user_and_password')
        self.type("%s\t\t%s\n" % (self.args.password, self.args.password))

        if self.args.language == 'eng':
            """
            # Configure the clock
            If the desired time zone is not listed, then please go back to the step "Choose language" and select a country that uses the desired time
            zone (the country where you live or are located).
            /Select your time zone:
             Eastern <<
             Central
             Mountain
             Pacific
             Alaska
             Hawaii
             Arizona
             East Indiana
             Samoa

            [Bildschirmfoto]  [Zurück] [Weiter]
            """
            self.wait_for_text('configure_clock')
            # self.type('clock')
            self.type('\n')

        # Festplatte erkennen
        self.disk_setup()

        """
        # Basissystem installieren
        """

        """
        # Paketmanager konfigurieren
        """

        """
        # Zusätzliche Software installieren
        """
        sleep(50, "disk.partition install")

        """
        # GRUB-Bootloader auf einer Festplatte installieren
        """
        self.wait_for_text('GRUB', timeout=1300)
        self.click_on('GRUB')
        self.client.keyPress('enter')

        """
        # Configure Univention System Setup
        """

        """
        # Installation abschließen
        /Installation abgeschlossen/
        Die Installation ist abgeschlossen und es ist an der Zeit, Ihr neues System zu starten. Achten Sie
        darauf, das Installationsmedium zu entfernen, so dass Sie das neue System starten statt einer
        erneuten Installation.

        [Bildschirmfoto]  [Zurück] [Weiter]
        """
        self.wait_for_text('finish_installation', timeout=-1300)
        self.click_on('continue')
        sleep(30, "reboot")

    @verbose("DISK")
    def disk_setup(self) -> None:
        """
        # Festplatte partitionieren
        Der Installer kann Sie durch die Partitionierung einer Festplatte (mit verschiedenen Standardschemata)
        führen. Wenn Sie möchten, können Sie dies auch von Hand tun. Bei Auswahl der geführten
        Partitionierung können Sie die Einstellungen später noch einsehen und anpassen.
        Falls Sie eine geführte Partitionierung für eine vollständige Platte wählen, werden Sie gleich danach
        gefragt, welche Platte verwendet werden soll.
        /Partitionierungsmethode:/
         Geführt - vollständige Festplatte verwenden
         Geführt - gesamte Platte verwenden und LVM einrichten <<
         Geführt - gesamte Platte mit verschlüsseltem LVM
         Manuell

        [Bildschirmfoto]  [Zurück] [Weiter]
        """
        self.wait_for_text('partition_disks')
        sub = getattr(self, "_disk_%s" % (self.args.role,), self._disk_default)
        sub()

    def _disk_applianceLVM(self) -> None:
        # self.click_on('entire_disk_with_lvm')
        # LVM is the default so just press enter
        self.type('\n')

        """
        # Festplatte partitionieren
        Beachten Sie, dass alle Daten auf der Festplatte, die Sie wählen, gelöscht werden, jedoch nicht, bevor Sie bestätigt haben, dass Sie die
        Änderungen wirklich durchführen möchten.
        /Wählen Sie die zu partitionierende Festplatte:
         SCSI (0,0,0) (sda) - QEMU QEMU HARDDISC: 10.7 GB

        [Bildschirmfoto]  [Zurück] [Weiter]
        """
        self.wait_for_text('choose_disk')
        self.type('\n')

        """
        # Festplatte partitionieren
        Für Partitonierung gewählt:

         SCSI (0,0,0) (sda) - QEMU QEMU HARDDISC: 10.7 GB

        Es gibt verschiedene Möglichkeiten, ein Laufwerk zu partitionieren. Wenn Sie sich nicht sicher sind, wählen Sie den ersten Eintrag.
        /Partitionierungsschema:/
         Alle Dateien auf eine Partition, für Anfänger empfohlen
         Separate /home-Partition

        [Bildschirmfoto]  [Zurück] [Weiter]
        """
        self.click_on('all_files_on_partition')
        self.type('\n')

        """
        # Festplatten partitionieren
        Bevor der Logical Volume Manager konfiguriert werden kann, muss die Aufteilung der Partitionen auf die Festplatte geschrieben
        werden. Diese Änderungen können nicht rückgängig gemacht werden.
        Nachdem der Logical Volume Manager konfiguriert ist, sind während der Installation keine weiteren Änderungen an der Partitionierung
        der Festplatten, die physikalische Volumes enthalten, erlaubt. Bitte überzeugen Sie sich, dass die Einteilung der Partitionen auf diesen
        Festplatten richtig ist, bevor Sie fortfahren.
        Die Partitionstabellen folgender Geräte wurden geändert:
         SCSI1 (0,0,0) (sda)
        /Änderungen auf die Speichergeräte schreiben und LVM einrichten?/
         (x) Nein
         ( ) Ja

        [Bildschirmfoto]  [Weiter]
        """
        self.wait_for_text("confirm_disk")
        self.client.keyPress('down')
        self.type('\n')

        """
        # Festplatte partitionieren
        Wenn Sie fortfahren, werden alle unten aufgeführten Änderungen auf die Festplatte(n) geschrieben. Andernfalls können Sie weitere
        Änderungen manuell durchführen.

        Die Partitionstabelle folgender Geräte wurden geändert:
         LVM VG vg_ucs, LV root
         LVM VG vg_ucs, LV swap_1
         SCSI1 (0,0,0) (sda)

        Die folgenden Partitionen werden formatiert:
         LVM VG vg_ucs, LV root als ext4
         LVM VG vg_ucs, LV swap_1 als Swap
         Partition 1 auf SCSI1 (0,0,0) (sda) als ext2

        /Änderungen auf die Festplatte schreiben?/
        (x) Nein
        ( ) Ja

        [Bildschirmfoto]  [Zurück] [Weiter]
        """
        self.wait_for_text('continue_partition')
        self.client.keyPress('down')
        self.type('\n')

    def _disk_applianceEC2(self) -> None:
        # Manuel
        self.click_on('manual')
        self.type('\n')

        """
        # Festplatte partitionieren
        Dies ist eine Übersicht über ihre konfigurierten Partitionen und Einbindepunkte. Wählen Sie eine Partition, um Änderungen vorzunehmen (Dateisystem,
        Einbindepunkte, usw.), freien Speicher, um Partitionen anzulegen oder ein gerät, um eine Partitionstabelle zu erstellen.
         Geführte Partitionierung
         iSCSI-Volumes konfigurieren

         SCSI (0,0,0) (sda) - 10.7 GB QEMU QEMU HARDDISK

         Änderungen an den Partitionen rückgängig machen
         Partitionierung beenden und Änderungen übernehmen

        [Bildschirmfoto] [Hilfe]  [Zurück] [Weiter]
        """
        self.wait_for_text('finish_partition')
        self.client.keyPress('down')
        self.client.keyPress('down')
        self.client.keyPress('down')
        self.type('\n')

        """
        # Festplatte partitionieren
        Sie haben ein komplettes Laufwerk zur Partitionierung angegeben. Wenn Sie fortfahren und eine neue Partitionstabelle anlegen,
        werden alle darauf vorhandenen Partitionen gelöscht.
        Beachten Sie, dass Sie diese Änderung später rückgängig machen können.
        /Neue, leere Partitionstabelle auf diesem Gerät erstellen?/
         (x) Nein
         ( ) Ja

        [Bildschirmfoto]  [Zurück] [Weiter]
        """
        self.wait_for_text("parition_new")
        self.client.keyPress('down')
        self.type('\n')

        """
        # Festplatte partitionieren
        Dies ist eine Übersicht über ihre konfigurierten Partitionen und Einbindepunkte. Wählen Sie eine Partition, um Änderungen vorzunehmen (Dateisystem,
        Einbindepunkte, usw.), freien Speicher, um Partitionen anzulegen oder ein gerät, um eine Paritionstabelle zu erstellen.
         Geführte Partitionierung
         Software-RAID konfigurieren
         Logical Volume Manager konfigurieren
         Verschlüsselte Datenträger konfigurieren
         iSCSI-Volumes konfigurieren

         SCSI (0,0,0) (sda) - 10.7 GB QEMU QEMU HARDDISK
          > pri/log 10.7 GB  FREIER SPEICHER

         Änderungen an den Partitionen rückgängig machen
         Partitionierung beenden und Änderungen übernehmen

        [Bildschirmfoto] [Hilfe]  [Zurück] [Weiter]
        """
        self.click_on('free_space')
        self.type('\n')

        """
        # Festplatte partitionieren
        /Wie mit freiem Speicher verfahren:/
         Eine neue Partition erstellen
         Freien Speicher automatisch partitionieren
         Anzeigen der Zylinder-/Kopf-/Sektor-Informationen

        [Bildschirmfoto] [Hilfe]  [Zurück] [Weiter]
        """
        self.wait_for_text("disk_free")
        self.type('\n')

        """
        # Festplatte partitionieren
        Die maximale Größe für diese Partition beträgt 10.7 GB.
        Tipp: »max« kann als Kürzel verwendet werden, um die maximale Größe anzugeben. Alternativ kann eine prozentuale Angabe (z.B.
        »20%«) erfolgen, um die Größe relativ zum Maximum anzugeben.
        /Neue Größe der Partition:/
         [10.7 GB]

        [Bildschirmfoto] [Hilfe]  [Zurück] [Weiter]
        """
        self.wait_for_text("parition_size")
        # enter: ganze festplattengröße ist eingetragen
        self.type('\n')

        """
        # Festplatte partitionieren
        /Typ der neuen Partition:/
         Primär
         Logisch

        [Bildschirmfoto] [Hilfe]  [Zurück] [Weiter]
        """
        self.wait_for_text("parition_type")
        # enter: primär
        self.type('\n')

        """
        # Festplatte partitionieren
        Sie bearbeiten Partition 1 auf SCSI1 (0,0,0) (sda). Auf dieser Partition wurde kein vorhandenes Dateisystem gefunden.
        /Partitionseinstellungen:
         Benutzen als: Ext4-Journaling-Dateisystem

         Einbindepunkt: /
         Einbindeoptionen: defaults
         Name: Keiner
         Reservierte Blöcke: 5%
         Typische Nutzung: standard
         Boot-Flag (Boot-fähig-Markierung): Aus

         Die Partition löschen
         Anlegen der Partition beenden

        [Bildschirmfoto] [Hilfe]  [Zurück] [Weiter]
        """
        self.click_on('boot_flag')
        # enter: boot-flag aktivieren
        self.type('\n')

        self.click_on('finish_create_partition')
        self.type('\n')

        """
        # Festplatte partitionieren
        Dies ist eine Übersicht über ihre konfigurierten Partitionen und Einbindepunkte. Wählen Sie eine Partition, um Änderungen vorzunehmen (Dateisystem,
        Einbindepunkte, usw.), freien Speicher, um Partitionen anzulegen oder ein gerät, um eine Partitionstabelle zu erstellen.
         Geführte Partitionierung
         Software-RAID konfigurieren
         Logical Volume Manager konfigurieren
         Verschlüsselte Datenträger konfigurieren
         iSCSI-Volumes konfigurieren

         SCSI (0,0,0) (sda) - 10.7 GB QEMU QEMU HARDDISK
          > Nr. 1 primär 10.7 GB B f ext4 /

         Änderungen an den Partitionen rückgängig machen
         Partitionierung beenden und Änderungen übernehmen

        [Bildschirmfoto] [Hilfe]  [Zurück] [Weiter]
        """
        self.click_on('finish_partition')
        self.type('\n')

        """
        # Festplatten partitionieren
        Sie haben keine Partition zur Verwendung als Swap-Speicher ausgewählt. Dies wird aber empfohlen, damit der Computer den
        vorhandenen Arbeitsspeicher effektiver nutzen kann, besonders wenn er knapp ist. Sie könnten Probleme bei der Installation
        bekommen, wenn Sie nicht genügend physikalischen Speicher haben.
        Wenn Sie nicht zum Partitionierungsmenü zurückkehren und eine Swap-Partition anlegen, wird die Installation ohne Swap-Speicher
        fortgesetzt.
        /Möchten Sie zum Partitionierungsmenü zurückkehren?/
          ( ) Nein
          (x) Ja

        """
        self.click_on('no')
        self.type('\n')

        """
        # Festplatte partitionieren
        Wenn Sie fortfahren, werden alle unten aufgeführten Änderungen auf die Festplatte(n) geschrieben. Andernfalls können Sie weitere
        Änderungen manuell durchführen.

        Die Partitionstabelle folgender Geräte wurden geändert:
         SCSI1 (0,0,0) (sda)

        Die folgenden Partitionen werden formatiert:
         Partition 1 auf SCSI1 (0,0,0) (sda) als ext4

        /Änderungen auf die Festplatte schreiben?
         (x) Nein
         ( ) Ja

        [Bildschirmfoto]  [Weiter]
        """
        self.wait_for_text('continue_partition')
        self.client.keyPress('down')
        self.type('\n\n')

    def _disk_default(self) -> None:
        self.click_on('entire_disk')
        self.type('\n')

        """
        # Festplatte partitionieren
        Beachten Sie, dass alle Daten auf der Festplatte, die Sie wählen, gelöscht werden, jedoch nicht, bevor Sie bestätigt haben, dass Sie die
        Änderungen wirklich durchführen möchten.
        /Wählen Sie die zu partitionierende Festplatte:/
          SCSI1 (0,0,0) (sda) - 10.7 GB QEMU QEMU HARDDISK

        [Bildschirmfoto]  [Zurück] [Weiter]
        """
        self.wait_for_text('choose_disk')
        self.type('\n')

        """
        # Festplatte partitionieren
        Für Partitonierung gewählt:

         SCSI (0,0,0) (sda) - QEMU QEMU HARDDISC: 10.7 GB

        Es gibt verschiedene Möglichkeiten, ein Laufwerk zu partitionieren. Wenn Sie sich nicht sicher sind, wählen Sie den ersten Eintrag.
        /Partitionierungsschema:/
         Alle Dateien auf eine Partition, für Anfänger empfohlen
         Separate /home-Partition

        [Bildschirmfoto]  [Zurück] [Weiter]
        """
        self.click_on('all_files_on_partition')
        self.type('\n')

        """
        # Festplatte partitionieren
        /Dies ist eine Übersicht über Ihre konfigurierten Partitionen und Einbindepunkte. Wählen Sie eine Partition, um
        Änderungen vorzunehmen (Dateisystem, Einbindepunkt, usw.), freien Speicher, um Partitionen anzulegen oder ein
        Gerät, um eine Partitionstabelle zu erstellen./
         Geführte Partitionierung
         Software-RAID konfigurieren
         Logical-Volume Manager konfigurieren
         Verschlüsselte Datenträger konfigurieren
         iSCSI-Volumes konfigurieren
         SCSI (0,0,0) (sda) - 21.5 GB QEMU QEMU HARDDISK
          > Nr. 1 primär  20.4 GB f ext4 /
          > Nr. 5 logisch  1.0 GB f swap Swap
         Änderungen an den Partitionen rückgängig machen
         Partitionierung beeenden und Änderungen übernehmen

        [Bildschirmfoto] [Hilfe]  [Zurück] [Weiter]
        """
        self.click_on('finish_partition')
        self.type('\n')

        """
        # Festplatte partitionieren
        Wenn Sie fortfahren, werden alle unten aufgeführten Änderungen auf die Festplatte(n) geschrieben.
        Andernfalls können Sie weitere Änderungen manuell durchführen.
        Die Partitionstabellen folgender Geräte wurden geändert:
         SCSI1 (0,0,0) (sda)
        Die folgenden Partitionen werden formatiert:
         Partition 1 auf SCSI1 (0,0,0) (sda) als ext4
         Partition 5 auf SCSI1 (0,0,0) (sda) als Swap
        /Änderungen auf die Festplatten schreiben?
         (x) Nein
         ( ) Ja
        [Bildschirmfoto] [Hilfe]  [Zurück] [Weiter]
        """
        self.wait_for_text('continue_partition')
        self.client.keyPress('down')
        self.type('\n')

    @verbose("NETWORK")
    def network_setup(self) -> None:
        """
        # Netzwerk einrichten
        Ihr System besitzt mehrere Netzwerk-Schnittstellen. Bitte wählen Sie die Schnittstelle (Netzwerkkarte),
        die für die Installation genutzt werden soll. Falls möglich, wurde die erste angeschlossene Schnittstelle
        ausgewählt.
        /Primäre Netzwerk-Schnittstelle:/
         enp1s0: Unbekannte Schnittstelle
         enp7s0: Unbekannte Schnittstelle

        [Bildschirmfoto]  [Zurück] [Weiter]
        """
        self.wait_for_text('configure_network')
        if not self.text_is_visible('ip_address'):
            # always use first interface
            self.click_on('continue')
            sleep(60, "net.detect")

        if not self.args.ip:
            raise ValueError("No IP address")

        if self.text_is_visible('not_using_dhcp'):
            """
            # Netzwerk einrichten
            /Die automatische Netzwerkkonfiguration ist fehlgeschlagen/
            Ihr Netzwerk benutzt möglicherweise nicht das DHCP-Protokoll. Des Weiteren könnte der DHCP-
            Server sehr langsam sein oder die Netzwerk-Hardware arbeitet nicht korrekt.
            [Bildschirmfoto] [Weiter]
            """
            self.type('\n')

            """
            # Netzwerk einrichten
            Hier können Sie wählen, die automatische DHCP-Netzwerkkonfiguration erneut zu versuchen (was
            funktionieren könnte, wenn Ihr DHCP-Server sehr langsam reagiert) oder das Netzwerk manuell zu
            konfigurieren. Manche DHCP-Server erfordern, dass der Client einen speziellen DHCP-Rechnernamen
            sendet, daher können Sie auch wählen, die automatische DHCP-Netzwerkkonfiguration mit Angabe eines
            Rechnernamens erneut zu versuchen.
            /Netzwerk-Konfigurationsmethode:/
             Autom. Konfiguration erneut versuchen
             Autom. Konfiguration erneut versuchen mit einem DHCP-Rechnernamen
             Netzwerk manuell einrichten
             Temporär eine Link-local-Adresse (169.254.0.0/16) verwenden

            [Bildschirmfoto]  [Zurück] [Weiter]
            """
            self.click_on('manual_network_config')
            self.type('\n')

        self.wait_for_text('ip_address')
        self.type(self.args.ip + "\n")
        if self.args.netmask:
            self.type(self.args.netmask)

        self.type('\n')
        self.wait_for_text('gateway')
        if self.args.gateway:
            self.type(self.args.gateway)

        self.type('\n')
        self.wait_for_text('name_server')
        if self.args.dns:
            self.type(self.args.dns)

        self.type('\n')

    def _network_repo(self):
        sleep(120, "net.dns")
        if self.text_is_visible('repositories_not_reachable'):
            self.type('\n')
            sleep(30, "net.dns2")

    @verbose("SETUP")
    def setup(self) -> None:
        """
        # Domäneneinstellungen
        Bitte wählen Sie die Domäneneinstellungen.

          Erstellen einer neuen UCS-Domäne  Empfohlen
            Dieses System als erstes System einer neuen Domäne einrichten. Zusätzliche Systeme können der Domäne später beitreten.
          Einer bestehenden UCS-Domäne beitreten
            Wählen Sie diese Option, falls bereits mindestens ein UCS-System existiert.
          Einer bestehenden Microsoft Active-Directory-Domäne beitreten
            Dieses System wird Teil einer existierenden nicht-UCS Active-Directory-Domäne.

        [Weiter]
        """
        self.wait_for_text('domain_setup', timeout=-300)
        sub = getattr(self, "_setup_%s" % (self.args.role,))
        sub()

    def _setup_master(self) -> None:
        self.click_on('new_domain')
        self.go_next()
        self.wait_for_text('account_information')
        """
        # Kontoinformationen
        Geben Sie den Namen ihrer Organisation und eine E-Mail-Adresse für die Aktivierung von UCS ein.

          Name der Organisation
          E-Mail-Adresse zur Aktivierung von UCS (mehr Informationen)

        [Zurück] [Weiter]
        """
        self.type('home')
        self.go_next()

    def _setup_joined(self, role_text: str) -> None:
        self.click_on('join_domain')
        self.go_next()
        if self.text_is_visible('no_dc_dns'):
            self.click_on('change_settings')
            self.click_on('preferred_dns')
            self.type(self.args.dns + "\n")
            self._network_repo()
            self.click_on('join_domain')
            self.go_next()

        self.wait_for_text('role')
        self.click_on(role_text)
        self.go_next()

    def _setup_backup(self) -> None:
        self._setup_joined('Backup Directory Node')

    def _setup_slave(self) -> None:
        self._setup_joined('Replica Directory Node')

    def _setup_member(self) -> None:
        self._setup_joined('Managed Node')

    def _setup_admember(self) -> None:
        self.click_on('ad_domain')
        self.go_next()
        self.wait_for_text('no_dc_dns')
        self.type('\n')
        self.click_on('preferred_dns')
        self.type(self.args.dns + "\n")
        self._network_repo()
        self.check_apipa()
        self.go_next()
        self.go_next()

    def _setup_applianceEC2(self) -> None:
        self.client.keyDown('ctrl')
        self.client.keyPress('w')  # Ctrl-Q
        self.client.keyUp('ctrl')
        """
        Close window and quit Firefox?
        [x] Confirm before quitting with Ctrl-Q
        [Cancel] [Quit Firefox]
        """
        if self.text_is_visible("Close windows and quit Firefox?", timeout=-3):
            self.type('\n')

        self.wait_for_text('univention')
        raise SystemExit(0)

    _setup_applianceLVM = _setup_applianceEC2

    def joinpass_ad(self) -> None:
        if self.args.role not in {'admember'}:
            return
        # join/ad password and user
        self.wait_for_text('ad_account_information')
        self.click_on('address_ad')
        self.type("\t")
        self.type(self.args.join_user + "\t", clear=True)
        self.type(self.args.join_password, clear=True)
        self.go_next()

    @verbose("JOIN")
    def joinpass(self) -> None:
        if self.args.role not in {'slave', 'backup', 'member'}:
            return
        self.wait_for_text('start_join')
        self.click_on('hostname_primary')
        self.type('\t')
        self.type(self.args.join_user + "\t", clear=True)
        self.type(self.args.join_password, clear=True)
        self.go_next()

    def hostname(self) -> None:
        """
        # Rechnereinstellungen
        Eingabe des Namens dieses Systems.

          Vollqualifizierter Domänenname: *
          LDAP-Basis *

        [Zurück] [Weiter]
        """
        if self.args.role == 'master':
            self.wait_for_text('host_settings')
        else:
            self.wait_for_text('system_name')

        self.type(self.args.fqdn, clear=True)
        if self.args.role == 'master':
            self.type('\t')

        self.go_next()

    def ucsschool(self) -> None:
        # ucs@school role
        if not self.args.school_dep:
            return

        self.wait_for_text('school_role')
        self.click_on('school_%s' % (self.args.school_dep,))
        self.go_next()

    @verbose("FINISH")
    def finish(self) -> None:
        """
        # Bestätigen der Einstellungen
        Bitte bestätigen Sie die gewählten Einstellungen, die nachstehend zusammengefasst sind.

          UCS-Konfiguration: Eine neue UCS-Domäne wird erstellt.
          Kontoinformationen
          * Name der Organisation: ...
          Domänen- und Rechnereinstellung
          * Vollqualifizierter Domänenname: ...
          * LDAP-Basis: ...
          [x] System nach der Einrichtung aktualisieren (mehr Informationen)
          Mit der Inbetriebnahme von UCS willigen Sie in unsere Datenschutzerklärung ein.

        [Zurück] [System konfigurieren]
        """
        self.wait_for_text('confirm_config')
        self.type('\n')
        sleep(self.setup_finish_sleep, "FINISH")

        """
        # UCS-Einrichtung erfolgreich
          UCS wurde erfolgreich eingerichtet.
          Klicken Sie auf /Fertigstellen/, um UCS in Betrieb zu nehmen.

        [Fertigstellen]
        """
        for i in range(3):
            try:
                self.wait_for_text('setup_successful', timeout=-2100)
            except Exception:  # vncdotool.client.VNCDoException:
                sleep(self.setup_finish_sleep, "FINISH")
        self.type('\t\n')
        self.wait_for_text('univention')

    @verbose("KVM")
    def configure_kvm_network(self, iface: str) -> None:
        self.wait_for_text('corporate server')
        self.type('\n')
        sleep(3)
        self.type('root\n')
        sleep(5)
        self.type(self.args.password + "\n")
        self.type('ucr set interfaces-%s-tzpe`manual\n' % iface)
        sleep(30, "kvm.ucr")
        self.type('ip link set %s up\n' % iface)
        self.type('echo ')
        self.client.keyDown('shift')
        self.type('2')  # @
        self.client.keyUp('shift')
        self.type('reboot -sbin-ip link set %s up ' % iface)
        self.client.keyDown('shift')
        self.type("'")  # |
        self.client.keyUp('shift')
        self.type(' crontab\n')

    @verbose("NEXT")
    def go_next(self) -> None:
        self.click_at(910, 700)


def main() -> None:
    parser = ArgumentParser(
        description=__doc__,
        parents=[build_parser()],
        formatter_class=ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        '--language',
        choices=['deu', 'eng', 'fra'],
        default="deu",
        help="Select text language",
    )
    parser.add_argument(
        "--role",
        default="master",
        choices=["master", "backup", "slave", "member", "admember", "applianceEC2", "applianceLVM"],
        help="UCS system role",
    )
    parser.add_argument(
        "--school-dep",
        choices=["central", "edu", "adm"],
        help="Select UCS@school role",
    )

    group = parser.add_argument_group("Network settings")
    group.add_argument(
        "--ip",
        help="IPv4 address if DHCP is unavailable",
    )
    group.add_argument(
        "--netmask",
        help="Network netmask",
    )
    group.add_argument(
        "--gateway",
        help="Default router address",
        metavar="IP",
    )
    parser.add_argument(
        "--second-interface",
        help="configure second interface",
        metavar="IFACE",
    )
    args = parser.parse_args()

    if args.role in {'slave', 'backup', 'member', 'admember'}:
        assert args.dns is not None
        assert args.join_user is not None
        assert args.join_password is not None

    inst = UCSInstallation(args=args)
    inst.run()


if __name__ == '__main__':
    main()
