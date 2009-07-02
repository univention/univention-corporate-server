#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
lang = sys.argv[1]


trans = {
	"Additional locales:" : { 'de' : "Weitere Sprachen:" },
	"An error has occurred. The additional system locales could not be generated." : { 'de' : "Ein Fehler ist aufgetreten. Die weiteren Sprachen konnten nicht erstellt werden." },
	"An error has occurred. The default system locale could not be generated." : { 'de' : "Ein Fehler ist aufgetreten. Die standard Sprache konnte nicht erstellt werden." },
	"An error has occurred. The keymap could not be set." : { 'de' : "Ein Fehler ist aufgetreten. Das Tastautlayout konnte nicht gesetzt werden.:" },
	"An internal Error has occurred." : { 'de' : "Ein interner Fehler ist aufgetreten." },
	"An internal Error has occurred - missing parameter." : { 'de' : "Ein interner Fehler ist aufgetreten - es fehlen Parameter." },
	"Back" : { 'de' : "Zurück" },
	"Cancel" : { 'de' : "Abbrechen" },
	"Change the localization settings" : { 'de' : "Anpassen der Lokalisierung" },
	"Default locale:" : { 'de' : "Standard Sprache:" },
	"Error message: %s" : { 'de' : "Fehlermeldung: %s" },
	"Keyboard layout:" : { 'de' : "Tastaturlayout:" },
	"Localization" : { 'de' : "Lokalisierung" },
	"Modification of the localization" : { 'de' : "Bearbeiten der Lokalisierung"},
	"Modify localization" : { 'de' : "Lokalisierung bearbeiten"},
	"Next" : { 'de' : "Weiter" },
	"Please choose your preferred language:" : { 'de' : "Bitte wählen Sie Ihre bevorzugte Sprache:" }, 
	"Selection of the preferred language" : { 'de' : "Auswahl der bevorzugten Sprache"},
	"Show all available locales" : { 'de' : "Alle verfügbaren Sprachen anzeigen" },
	"Show all available timezones" : { 'de' : "Alle verfügbaren Zeitzonen anzeigen" },
	"The following scripts failed: %(scripts)" : { 'de' : "Die folgenden Skripte schulgen fehl: %(scripts)" },
	"Timezone:" : { 'de' : "Zeitzone:" },
	"Unknown locale - %s" : { 'de' : "Unbekannte Sprache - %s" },
	"Unknown language code %s (%s)" : { 'de' : "Unbekannter Sprachcode %s (%s)"},
	"Warning: The Univention-Config-Registry variable locale/default contains the unsupported locale '%s'." : { 'de' : "Warnung: Die Univention-Config-registry Variable locale/default enthält die nicht unterstützte Sprache '%s'." },
	"Warning: The Univention-Config-Registry variable 'locale' contains the unsupported value '%s'." : { 'de' : "Zeitzone:" },
} 

for key in trans:
	if lang in trans[key]:
		print "msgid \"%s\"" % key
		print "msgstr \"%s\"" % trans[key][lang]

