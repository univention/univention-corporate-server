<?php
/**
 * Horde_Form_Action_ConditionalSetValue is a Horde_Form_Action that
 * sets the value of one Horde_Form variable based on the value of the
 * variable the action is attached to.
 *
 * $Horde: framework/Form/Form/Action/ConditionalSetValue.php,v 1.2.2.3 2009-01-06 15:23:07 jan Exp $
 *
 * Copyright 2002-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @package Horde_Form
 */
class Horde_Form_Action_ConditionalSetValue extends Horde_Form_Action {

    /**
     * Which JS events should trigger this action?
     *
     * @var array
     */
    var $_trigger = array('onchange', 'onload');

    function getActionScript($form, $renderer, $varname)
    {
        return 'map(\'' . $renderer->_genID($varname, false) . "', '" . $renderer->_genID($this->getTarget(), false) . '\');';
    }

    function setValues(&$vars, $sourceVal, $arrayVal = false)
    {
        $map = $this->_params['map'];
        $target = $this->getTarget();

        if ($arrayVal) {
            $i = 0;
            if (is_array($sourceVal)) {
                foreach ($sourceVal as $val) {
                    if (!empty($map[$val])) {
                        $vars->set($target, $map[$val], $i);
                    }
                    $i++;
                }
            }
        } else {
            if (!empty($map[$sourceVal])) {
                $vars->set($target, $map[$sourceVal]);
            }
        }
    }

    function printJavaScript()
    {
        $this->_printJavaScriptStart();
        $map = $this->_params['map'];
?>

var _map = [<?php
$i = 0;
foreach ($map as $val) {
    if ($i > 0) {
        echo ', ';
    }
    echo '"' . $val . '"';
    $i++;
}?>];

function map(sourceId, targetId)
{
    var newval;
    var source = document.getElementById(sourceId);
    var element = document.getElementById(targetId);
    if (element) {
        if (_map[source.selectedIndex]) {
            newval = _map[source.selectedIndex];
            replace = true;
        } else {
            newval = '';
            replace = false;
            for (i = 0; i < _map.length; i++) {
                if (element.value == _map[i]) {
                    replace = true;
                    break;
                }
            }
        }

        if (replace) {
            element.value = newval;
        }
    }
}<?php
        $this->_printJavaScriptEnd();
    }

}
