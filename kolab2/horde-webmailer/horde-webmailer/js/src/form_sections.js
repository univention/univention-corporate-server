/**
 * Horde Form Sections Javascript Class
 *
 * Provides the javascript class for handling tabbed sections in Horde Forms.
 *
 * Copyright 2003-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * $Horde: horde/js/src/form_sections.js,v 1.6.2.4 2009-05-12 07:12:58 jan Exp $
 *
 * @author  Marko Djukic <marko@oblo.com>
 * @package Horde_Form
 */
function Horde_Form_Sections(instanceName, openSection)
{
    /* Set up this class instance for function calls from the page. */
    this._instanceName = instanceName;

    /* The currently showed section. */
    var _openSection, s;

    this.toggle = function(sectionId)
    {
        if (!document.getElementById) {
            return false;
        }

        /* Get the currently open section object. */
        openSectionId = this._get();
        s = document.getElementById(this._instanceName + '_section_' + openSectionId);
        if (s) {
            s.style.display = 'none';
            document.getElementById(this._instanceName + '_tab_' + openSectionId).className = null;
        }

        /* Get the newly opened section object. */
        s = document.getElementById(this._instanceName + '_section_' + sectionId);
        if (s) {
            s.style.display = '';
            document.getElementById(this._instanceName + '_tab_' + sectionId).className = 'activeTab';
        }

        /* Store the newly opened section. */
        this._set(sectionId);
    }

    this._get = function()
    {
        return this._openSection;
    }

    this._set = function(sectionId)
    {
        var form = document.getElementById(this._instanceName);
        if (form != null &&
            typeof form.__formOpenSection != 'undefined') {
            form.__formOpenSection.value = sectionId;
        }
        this._openSection = sectionId;
    }

    this._set(openSection);
}
