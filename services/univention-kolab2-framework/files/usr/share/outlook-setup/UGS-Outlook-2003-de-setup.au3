; Univention UGS Outlook 2003 Setup
;  AutoIT(tm) script for configuration Outlook 2003 as UGS client
;
; Copyright (C) 2006-2009 Univention GmbH
;
; http://www.univention.de/
;
; All rights reserved.
;
; This program is free software; you can redistribute it and/or modify
; it under the terms of the GNU General Public License version 2 as
; published by the Free Software Foundation.
;
; Binary versions of this file provided by Univention to you as
; well as other copyrighted, protected or trademarked materials like
; Logos, graphics, fonts, specific documentations and configurations,
; cryptographic keys etc. are subject to a license agreement between
; you and Univention.
;
; This program is distributed in the hope that it will be useful,
; but WITHOUT ANY WARRANTY; without even the implied warranty of
; MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
; GNU General Public License for more details.
;
; You should have received a copy of the GNU General Public License
; along with this program; if not, write to the Free Software
; Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA    02110-1301      USA

;GuiDatei einbinden
#include <GuiConstants.au3>

;Starten der Installation OK? Abbrechen? Nach 10 Sek. automatisch OK
;$answer = MsgBox(65,"Installation","Die automatische Konfiguration von Outlook2003 als UGS-Client starten?",10)
;If $answer = 2 Then	
;	Exit
;EndIf

;oeffnen der Konfigurationsdatei
If $CmdLine[0] = 1 Then
	$file = FileOpen($CmdLine[1],0)
Else	
	$file = FileOpen("konfig2003.txt", 0)
EndIf
;Zeilenweises einlesen der Konfigurationsdatei.
$name1 = FileReadLine($file,1)   
$name2 = FileReadLine($file,2)
$mail1 = FileReadLine($file,3)
$mail2 = FileReadLine($file,4)
$serv = FileReadLine($file,5)
$pwrd = FileReadLine($file,6)
$line0 = FileReadLine($file,7)
$ldap = FileReadLine($file,8)
$checkhow = FileReadLine($file,9)

;Konfigurationsdatei schliessen
FileClose($file)

If $checkhow = ("1") Then 
	$checkCNx = ("-1")
	$checkCNy = ("1")
	$checkUNx = ("0")
	$checkUNy = ("4")
ElseIf $checkhow = ("2") Then
	$checkCNx = ("0")
	$checkCNy = ("4")
	$checkUNx = ("-1")
	$checkUNy = ("1")
ElseIf $checkhow = ("3") Then
	$checkCNx = ("-1")
	$checkCNy = ("1")
	$checkUNx = ("-1")
	$checkUNy = ("1")
Else
	$checkCNx = ("-1")
	$checkCNy = ("1")
	$checkUNx = ("-1")
	$checkUNy = ("1")
EndIf

$pflicht=("")
$ctrl = ("")
If $name1 <> ("") And $name2 <> ("") And $mail1 <> ("") And $mail2 <> ("") And $serv <> ("") And $pwrd <> ("") And $line0 <> ("") Then $ctrl = ("ok")
	
While $name1 = ("") or $name2 = ("") or $mail1 = ("") or $mail2 = ("") or $serv = ("") or $pwrd = ("") or $ctrl = ("")
	
;Hauptfenster erstellen
GUICreate("Outlook 2003 als UGS-Client mit Toltec Connector",405,440)
GUICtrlCreateLabel("Tool zur automatisierten Konfiguration ","15","15")
GUICtrlCreateLabel("von Outlook2003 als UGS-Client mit","15","30")
GUICtrlCreateLabel("Toltec-Connector ","15","45")
;Univention-Logo
GuiCtrlCreatePic("univention_logo.gif",240,10,150,50)
If Not FileExists("univention_logo.gif") Then
	GuiCtrlCreateLabel("" & @CRLF & "              UNIVENTION" & @CRLF & "        linux for your business", 240, 10, 150, 50)
	GuiCtrlSetBkColor(-1, 0xcc0033)
	GUICtrlSetColor(-1,0xffffff)
EndIf

GUICtrlCreateLabel("Auswahl:",15,83)

$checkCN = GUICtrlCreateCheckbox ("Outlook konfigurieren", 110, 80, 120, 20)
GuiCtrlSetState($checkCNx, $GUI_CHECKED)

$checkUN = GUICtrlCreateCheckbox ("Toltec konfigurieren", 270, 80, 120, 20)
GuiCtrlSetState($checkUNx, $GUI_CHECKED)

;Bezeichnung für folgende Eingabeaufforderung
GUICtrlCreateLabel("Name","15","123","60")
GUICtrlCreateLabel("*","47","123","","")
GUICtrlSetColor(-1,$pflicht) 
;Eingabeaufforderung mit Default-Wert
$line01 = GUICtrlCreateInput($name1,"110","120","100","","")
If $name1 = ("") Then
	GUICtrlSetState(-1,$GUI_FOCUS)
EndIf
GUICtrlCreateLabel("Vorname","218","123","80")
GUICtrlCreateLabel("*","260","123")
GUICtrlSetColor(-1,$pflicht)
$line02 = GUICtrlCreateInput($name2,"270","120","120","","")

GUICtrlCreateLabel("E-Mail ","15","163")
GUICtrlCreateLabel("*","47","163")
GUICtrlSetColor(-1,$pflicht)
$line03 = GUICtrlCreateInput($mail1,"110","160","120","","")

GUICtrlCreateLabel("@","234","163", "160")
$line04 = GUICtrlCreateInput($mail2,"250","160","140","","")

GUICtrlCreateLabel("Server","15","203","60")
GUICtrlCreateLabel("*","47","203")
GUICtrlSetColor(-1,$pflicht)
$line05 = GUICtrlCreateInput ($serv,"110","200","280","","")

GUICtrlCreateLabel("Passwort","15","243","80")
GUICtrlCreateLabel("*","60","240")
GUICtrlSetColor(-1,$pflicht)
$line06 = GUICtrlCreateInput("","110","240","280","",$ES_PASSWORD)
If $name1 <> ("") Then
	GUICtrlSetState(-1,$GUI_FOCUS)
EndIf
GUICtrlCreateLabel("Passwortkontrolle","15","283","120")
GUICtrlCreateLabel("*","100","280")
GUICtrlSetColor(-1,$pflicht)
$chkline = GUICtrlCreateInput("","110","280","280","",$ES_PASSWORD)

GUICtrlCreateLabel("LDAP-Suchbasis","15","323","120")
$line07 = GUICtrlCreateInput($ldap,"110","320","280","","")

GUICtrlCreateLabel("* Pflichtfelder","325","345")
GUICtrlSetColor(-1,$pflicht)
;Ok-Button erstellen
$ok = GUICtrlCreateButton ("OK","110","380","80")
;Abbrechen-Button erstellen
$cancel = GUICtrlCreateButton ("Abbrechen","230","380","80")

GUICtrlCreateLabel("© UNIVENTION GmbH, 2006, www.univention.de, Version 1.01","15","425","420")

;Das Fenster öffnen
GUISetState()

While 1 
	
	$msg = GUIGetMsg()
	;warten auf welchen Button gedrückt wird
	if $msg = $Gui_Event_Close Then Exit
		
	if $msg = $cancel Then Exit
		
	if $msg = $ok Then ExitLoop
		
WEnd
	
;Die Benutzereingaben übernehmen und abspeichern
$name1 = GUICtrlRead($line01)
$name2 = GUICtrlRead($line02)
$mail1 = GUICtrlRead($line03)
$mail2 = GUICtrlRead($line04)
$serv = GUICtrlRead($line05)
$pwrd = GUICtrlRead($line06)
$pwchk = GUICtrlRead($chkline)
$ldap = GUICtrlRead($line07)
$checkCNy = GUICtrlRead($checkCN)
$checkUNy = GUICtrlRead($checkUN)


If $pwchk <> $pwrd Then
	$ctrl = ("")
Else
	$ctrl = ("ok")
EndIf
	
$pflicht = ("0xff0000")	
GUIDelete()
ContinueLoop
WEnd

If $line0 = ("") Then
	$offic = ("C:\Programme\Microsoft Office\OFFICE11\OUTLOOK.EXE")
	Else
		$offic = $line0
EndIf	
If Not FileExists($offic) Then
	MsgBox(64,"Fehler","Die Konfiguration wird abgebrochen, die Datei OUTLOOK.EXE konnte nicht gefunden werden.")
	Exit
EndIf
	
If $checkCNy = 1 Then	
;outlook starten
run ($offic)
Sleep (5000)
WinWait("Outlook 2003-Start")
Send ("{ENTER}")
WinWait("Konto konfigurieren")
Send ("{ENTER}")
Winwait ("E-Mail-Konten")
Send ("{DOWN}")
Send ("{ENTER}")
Winwait ("E-Mail-Konten")
;Die Benutzereingaben in die Dialogfelder eingeben
WinActivate("E-Mail-Konten")
Send ($name2)
WinActivate("E-Mail-Konten")
Send(" ")
WinActivate("E-Mail-Konten")
Send ($name1)
WinActivate("E-Mail-Konten")
Send ("{TAB}")
WinActivate("E-Mail-Konten")
Send ($mail1)
WinActivate("E-Mail-Konten")
Send ("@")
WinActivate("E-Mail-Konten")
Send ($mail2)
WinActivate("E-Mail-Konten")
Send ("{TAB}")
WinActivate("E-Mail-Konten")
Send ($serv)
WinActivate("E-Mail-Konten")
Send ("{TAB}")
WinActivate("E-Mail-Konten")
Send ($serv)
WinActivate("E-Mail-Konten")
Send ("{TAB}")
WinActivate("E-Mail-Konten")
Send ($mail1)
WinActivate("E-Mail-Konten")
Send ("@")
WinActivate("E-Mail-Konten")
Send ($mail2)
WinActivate("E-Mail-Konten")
Send ("{TAB}")
WinActivate("E-Mail-Konten")
Send ($pwrd)
Send ("{TAB}")
Send ("{TAB}")
Send ("{TAB}")
Send ("{TAB}")
WinActivate("E-Mail-Konten")
Send ("{SPACE}")
Send ("+{TAB}")
Send ("{RIGHT}")
Send ("{TAB}")
WinActivate("Internet-E-Mail-Einstellungen")
Send ("{SPACE}")
Send ("+{TAB}")
Send ("{RIGHT}")
Send ("{RIGHT}")
Send ("{TAB}")
Send ("{TAB}")
WinActivate("Internet-E-Mail-Einstellungen")
Send ("{SPACE}")
Send ("{TAB}")
Send ("{TAB}")
WinActivate("Internet-E-Mail-Einstellungen")
Send ("{SPACE}")
WinActivate("Internet-E-Mail-Einstellungen")
Send ("{ENTER}")
WinActivate("E-Mail-Konten")
Send ("{ENTER}")
WinActivate("E-Mail-Konten")
Send ("{ENTER}")
While 1
	Sleep(3000)
	If WinActive ("Willkommen ") Then Send ("!F4")
	If WinActive ("Posteingang") Then ExitLoop
	If WinExists ("Benutzername") Then Send ("{ENTER}")
WEnd
Sleep(1000)
EndIf
If $checkUNy = 1 Then
	If Not WinExists("Posteingang") Then
		Run ($offic)
	EndIf
;Toltec einrichten. Achtung Lizenz muss Installiert sein!
WinwaitActive ("Posteingang")
Send ("!x")
Send ("o")
WinWait ("Optionen")
WinActivate("Optionen")
send ("+{TAB}")
Send ("{RIGHT}")
Send ("{RIGHT}")
Send ("{RIGHT}")
Send ("{RIGHT}")
Send ("{RIGHT}")
Send ("{RIGHT}")
WinWait("Optionen","Toltec")
WinActivate("Optionen")
ControlClick ( "Optionen", "Toltec", "Button2") 
Sleep(2000)
Send ("!w")
Send ("!w")
Send ("!w")
Send($serv)
send ("{TAB}")
Send ($mail1)
Send ("@")
Send ($mail2)
send ("{TAB}")
Send ($pwrd)
ControlEnable ( "Toltec Connector", "Sicherheit", "Button4" )
ControlClick ( "Toltec Connector", "Sicherheit", "Button4" )
Send ("{ENTER}")
Sleep (20000)
While 1
	If WinExists("Internetsicherheitshinweis") Then
		WinActivate("Internetsicherheitshinweis")
		Send ("{ENTER}")
	Else
		ExitLoop
	EndIf
Wend
Send ("!w")
Send ("{ENTER}")
Send ("{Tab}")
WinActivate("Optionen")
Send ("{ENTER}")
EndIf
If $checkCNy = 1 Then
;free-busy listen einrichten
Send ("!x")
Send ("o")
WinActivate("Optionen")
send ("{TAB}")
send ("{TAB}")
send ("{TAB}")
send ("{TAB}")
WinActivate("Optionen")
Send ("{ENTER}")
Send ("+{TAB}")
Send ("+{TAB}")
Send ("+{TAB}")
Send ("+{TAB}")
Send ("+{TAB}")
WinActivate("Kalenderoptionen")
Send ("{ENTER}")
WinActivate("Frei/Gebucht-Optionen")
send ("{TAB}")
send ("{TAB}")
send ("{TAB}")
send ("{TAB}")
WinActivate("Frei/Gebucht-Optionen")
Send ("http://")
Send ($serv)
Send ("/freebusy/%NAME%@%SERVER%.ifb")
WinActivate("Frei/Gebucht-Optionen")
Send ("{ENTER}")
WinActivate("Kalenderoptionen")
send ("{TAB}")
send ("{TAB}")
send ("{TAB}")
WinActivate("Kalenderoptionen")
Send ("{ENTER}")
WinWait ("Optionen")
Send ("{ESC}")
EndIf
;LDAP-Konfiguration
If $ldap <> ("") Then
WinActivate ("Posteingang")
Send ("!x")
Send ("m")
WinActivate("E-Mail-Konten")
send ("{i}")
WinActivate("E-Mail-Konten")
send ("{enter}")
WinActivate("E-Mail-Konten")
send ("{enter}")
WinActivate("E-Mail-Konten")
send ($serv)
WinActivate("E-Mail-Konten")
send ("!t")
send ("{enter}")
send ("+{TAB}")
Send ("{RIGHT}")
Send ("!u")
Send($ldap)
Send ("{ENTER}")
WinActivate("E-Mail-Konten")
Send ("{ENTER}")
WinActivate("E-Mail-Konten")
Send ("{ENTER}")
EndIf
Sleep (1000)
If $checkCNy <> ("1") And $checkUNy <> ("1") Then Exit
WinActivate ("Posteingang")
Send ("{ALT}")
Send("d")
Send("b")
Sleep (2000)
While 1
	If WinExists("Internetsicherheitshinweis") Then
		WinActivate("Internetsicherheitshinweis")
		Send ("{ENTER}")
	Else
		ExitLoop
	EndIf
Wend
MsgBox(64, "Installation Info", "Outlook2003 wurde als UGS-Client konfiguriert")
