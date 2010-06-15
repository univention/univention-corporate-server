<?php
/**
 * The Editor_htmlarea:: class provides an WYSIWYG editor for use
 * in the Horde Framework.
 *
 * $Horde: framework/Editor/Editor/htmlarea.php,v 1.14 2004/03/09 21:24:21 jan Exp $
 *
 * Copyright 2003-2004 Nuno Loureiro <nuno@co.sapo.pt>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Nuno Loureiro <nuno@co.sapo.pt>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 3.0
 * @package Horde_Editor
 */
class Horde_Editor_htmlarea extends Horde_Editor {

    /**
     * Constructor.
     * Include the necessary javascript files.
     */
    function Horde_Editor_htmlarea($params = array()) 
    {
        global $registry, $notification;

        Horde::addScriptFile('htmlarea.js', 'horde');
        Horde::addScriptFile('/services/editor/htmlarea/htmlarea.js', 'horde', true);
        Horde::addScriptFile('htmlarea_lang.js', 'horde');
        if (isset($params['id'])) {
            $js = 'HTMLArea.replace("' . $params['id'] . '");';
        } else {
            $js = 'HTMLArea.replaceAll();';
        }
        $notification->push($js, 'javascript');
    }
    
}
