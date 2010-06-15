/**
 * Horde Form Sections Javascript Class
 *
 * Provides the javascript class for handling tabbed sections in Horde Forms.
 *
 * Copyright 2003-2004 Marko Djukic <marko@oblo.com>
 *
 * See the enclosed file COPYING for license information (LGPL). If you did not
 * receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * $Horde: horde/templates/javascript/form_sections.js,v 1.6 2004/03/16 19:20:36 chuck Exp $
 *
 * @author  Marko Djukic <marko@oblo.com>
 * @version $Revision: 1.1.2.1 $
 * @package Horde_Form
 */
function Horde_Form_Sections(instanceName, openSection)
{
    /* Set up this class instance for function calls from the page. */
    this._instanceName = instanceName;

    /* Store the currently open section in a variable, as well as the
     * cookie. */
    this._openSection = openSection;

    /* The cookie name we'll use. */
    this._cookieName = this._instanceName + '_open';

    this.getThis = function()
    {
        return this;
    }

    this.toggle = function(sectionId)
    {
        /* Get the currently open section object. */
        openSectionId = this._get();
        if (document.getElementById('_section_' + openSectionId)) {
            document.getElementById('_section_' + openSectionId).style.display = 'none';
            document.getElementById('_tab_' + openSectionId).className = 'tab';
            document.getElementById('_tabLink_' + openSectionId).className = 'tab';
        }

        /* Get the newly opened section object. */
        if (document.getElementById('_section_' + sectionId)) {
            document.getElementById('_section_' + sectionId).style.display = 'block';
            document.getElementById('_tab_' + sectionId).className = 'tab-hi';
            document.getElementById('_tabLink_' + sectionId).className = 'tab-hi';
        }

        /* Store the newly opened section. */
        this._set(sectionId);
    }

    this._get = function()
    {
        var dc = document.cookie;
        var prefix = this._cookieName + '=';
        var begin = dc.indexOf('; ' + prefix);
        if (begin == -1) {
            begin = dc.indexOf(prefix);
            if (begin != 0) {
                return this._openSection;
            }
        } else {
            begin += 2;
        }

        var end = dc.indexOf(';', begin);
        if (end == -1) {
            end = dc.length;
        }

        return unescape(dc.substring(begin + prefix.length, end));
    }

    this._set = function(sectionId)
    {
        var cookieValue = this._cookieName + '=' + escape(sectionId);
        cookieValue += ';DOMAIN=<?php echo $GLOBALS['conf']['cookie']['domain'] ?>;PATH=<?php echo $GLOBALS['conf']['cookie']['path'] ?>;';
        document.cookie = cookieValue;
        this._openSection = sectionId;
    }

    this._set(openSection);
}
