<?php
/**
 * Horde_Form_Action_sum_fields is a Horde_Form_Action that sets the target
 * field to the sum of one or more other numeric fields.
 *
 * The params array should contain the names of the fields which will be
 * summed.
 *
 * $Horde: framework/Form/Form/Action/sum_fields.php,v 1.5.10.8 2009-01-06 15:23:07 jan Exp $
 *
 * Copyright 2002-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Matt Kynaston <matt@kynx.org>
 * @package Horde_Form
 */
class Horde_Form_Action_sum_fields extends Horde_Form_Action {

    var $_trigger = array('onload');

    function getActionScript(&$form, $renderer, $varname)
    {
        Horde::addScriptFile('form_helpers.js', 'horde', true);

        $form_name = $form->getName();
        $fields = "'" . implode("','", $this->_params) . "'";
        $js = array();
        $js[] = sprintf('document.forms[\'%s\'].elements[\'%s\'].disabled = true;',
                        $form_name,
                        $varname);
        foreach ($this->_params as $field) {
            $js[] = sprintf("addEvent(document.forms['%1\$s'].elements['%2\$s'], \"onchange\", \"sumFields(document.forms['%1\$s'], '%3\$s', %4\$s);\");",
                            $form_name,
                            $field,
                            $varname,
                            $fields);
        }

        return implode("\n", $js);
    }

}
