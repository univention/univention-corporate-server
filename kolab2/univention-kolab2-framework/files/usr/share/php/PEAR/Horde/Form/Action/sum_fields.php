<?php
/**
 * Horde_Form_Action_sum_fields is a Horde_Form_Action that sets the target
 * field to the sum of one or more other numeric fields.
 *
 * The params array should contain the names of the fields which will be
 * summed.
 *`
 * Copyright 2002-2004 Matt Kynaston <matt@kynx.org>
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
        Horde::addScriptFile('form_helpers.js', 'horde');
        $form_name = $form->getName();
        $fields = "'" . join("','", $this->_params) . "'";
        $js = array();
        $js[] = sprintf('document.%s.%s.disabled = true;',
                        $form_name,
                        $varname);
        foreach($this->_params as $field) {
            $js[] = sprintf("addEvent(document.%s.%s, 'onchange', \"sumFields(this.form, '%s', %s);\");",
                            $form_name,
                            $field,
                            $varname,
                            $fields);
        }
        return join("\n", $js);
    }
}
