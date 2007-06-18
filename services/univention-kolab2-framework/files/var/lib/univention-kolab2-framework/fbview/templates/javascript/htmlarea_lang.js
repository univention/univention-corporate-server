HTMLArea.I18N = {

	// the following should be the filename without .js extension
	// it will be used for automatically load plugin language.
	lang: "en",

	tooltips: {
		bold:           "<?php echo addslashes(_("Bold")) ?>",
		italic:         "<?php echo addslashes(_("Italic")) ?>",
		underline:      "<?php echo addslashes(_("Underline")) ?>",
		strikethrough:  "<?php echo addslashes(_("Strikethrough")) ?>",
		subscript:      "<?php echo addslashes(_("Subscript")) ?>",
		superscript:    "<?php echo addslashes(_("Superscript")) ?>",
		justifyleft:    "<?php echo addslashes(_("Justify Left")) ?>",
		justifycenter:  "<?php echo addslashes(_("Justify Center")) ?>",
		justifyright:   "<?php echo addslashes(_("Justify Right")) ?>",
		justifyfull:    "<?php echo addslashes(_("Justify Full")) ?>",
		orderedlist:    "<?php echo addslashes(_("Ordered List")) ?>",
		unorderedlist:  "<?php echo addslashes(_("Bulleted List")) ?>",
		outdent:        "<?php echo addslashes(_("Decrease Indent")) ?>",
		indent:         "<?php echo addslashes(_("Increase Indent")) ?>",
		forecolor:      "<?php echo addslashes(_("Font Color")) ?>",
		hilitecolor:    "<?php echo addslashes(_("Background Color")) ?>",
		horizontalrule: "<?php echo addslashes(_("Horizontal Rule")) ?>",
		createlink:     "<?php echo addslashes(_("Insert Web Link")) ?>",
		insertimage:    "<?php echo addslashes(_("Insert/Modify Image")) ?>",
		inserttable:    "<?php echo addslashes(_("Insert Table")) ?>",
		htmlmode:       "<?php echo addslashes(_("Toggle HTML Source")) ?>",
		popupeditor:    "<?php echo addslashes(_("Enlarge Editor")) ?>",
		about:          "<?php echo addslashes(_("About this editor")) ?>",
		showhelp:       "<?php echo addslashes(_("Help using editor")) ?>",
		textindicator:  "<?php echo addslashes(_("Current style")) ?>",
		undo:           "<?php echo addslashes(_("Undoes your last action")) ?>",
		redo:           "<?php echo addslashes(_("Redoes your last action")) ?>",
		cut:            "<?php echo addslashes(_("Cut selection")) ?>",
		copy:           "<?php echo addslashes(_("Copy selection")) ?>",
		paste:          "<?php echo addslashes(_("Paste from clipboard")) ?>",
		lefttoright:    "<?php echo addslashes(_("Direction left to right")) ?>",
		righttoleft:    "<?php echo addslashes(_("Direction right to left")) ?>"
	},

	buttons: {
		"ok":           "<?php echo addslashes(_("OK")) ?>",
		"cancel":       "<?php echo addslashes(_("Cancel")) ?>"
	},

	msg: {
		"Path":         "<?php echo addslashes(_("Path")) ?>",
		"TEXT_MODE":    "<?php echo addslashes(_("You are in TEXT MODE.  Use the [<>] button to switch back to WYSIWYG.")) ?>",

		"IE-sucks-full-screen" :
		// translate here
		"<?php echo addslashes(_("The full screen mode is known to cause problems with Internet Explorer, due to browser bugs that we weren't able to workaround.  You might experience garbage display, lack of editor functions and/or random browser crashes.  If your system is Windows 9x it's very likely that you'll get a 'General Protection Fault' and need to reboot.\\n\\nYou have been warned.  Please press OK if you still want to try the full screen editor.")) ?>",

		"Moz-Clipboard" :
		"<?php echo addslashes(_("Unprivileged scripts cannot access Cut/Copy/Paste programatically for security reasons.  Click OK to see a technical note at mozilla.org which shows you how to allow a script to access the clipboard.")) ?>"
	},

	dialogs: {
		"Cancel"                                            : "<?php echo addslashes(_("Cancel")) ?>",
		"Insert/Modify Link"                                : "<?php echo addslashes(_("Insert/Modify Link")) ?>",
		"New window (_blank)"                               : "<?php echo addslashes(_("New window (_blank)")) ?>",
		"None (use implicit)"                               : "<?php echo addslashes(_("None (use implicit)")) ?>",
		"OK"                                                : "<?php echo addslashes(_("OK")) ?>",
		"Other"                                             : "<?php echo addslashes(_("Other")) ?>",
		"Same frame (_self)"                                : "<?php echo addslashes(_("Same frame (_self)")) ?>",
		"Target:"                                           : "<?php echo addslashes(_("Target:")) ?>",
		"Title (tooltip):"                                  : "<?php echo addslashes(_("Title (tooltip):")) ?>",
		"Top frame (_top)"                                  : "<?php echo addslashes(_("Top frame (_top)")) ?>",
		"URL:"                                              : "<?php echo addslashes(_("URL:")) ?>",
		"You must enter the URL where this link points to"  : "<?php echo addslashes(_("You must enter the URL where this link points to")) ?>"
	}
};
