<?php

require_once 'Horde/UI/VarRenderer/html.php';

/**
 * Extension of Horde's variable renderer that support Ingo's folders variable
 * type.
 *
 * $Horde: ingo/lib/UI/VarRenderer/ingo.php,v 1.3.2.3 2009-01-06 15:24:37 jan Exp $
 *
 * Copyright 2006-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file LICENSE for license information (ASL).  If you
 * did not receive this file, see http://www.horde.org/licenses/asl.php.
 *
 * @author  Jan Schneider <jan@horde.org>
 * @package Ingo
 */
class Horde_UI_VarRenderer_ingo extends Horde_UI_VarRenderer_html {

    function _renderVarInput_ingo_folders(&$form, &$var, &$vars)
    {
        return Ingo::flistSelect($var->type->getFolder(), 'horde_form', 'folder');
    }

}
