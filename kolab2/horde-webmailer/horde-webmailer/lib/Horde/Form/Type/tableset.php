<?php

require_once 'Horde/Form.php';

/**
 * $Horde: framework/Form/Form/Type/tableset.php,v 1.3.2.2 2007-12-20 13:49:05 jan Exp $
 *
 * @package Horde_Form
 * @since   Horde 3.1
 */
class Horde_Form_Type_tableset extends Horde_Form_Type {

    var $_values;
    var $_header;

    function init($values, $header)
    {
        $this->_values = $values;
        $this->_header = $header;
    }

    function isValid(&$var, &$vars, $value, &$message)
    {
        if (count($this->_values) == 0 || count($value) == 0) {
            return true;
        }
        foreach ($value as $item) {
            if (!isset($this->_values[$item])) {
                $error = true;
                break;
            }
        }
        if (!isset($error)) {
            return true;
        }

        $message = _("Invalid data submitted.");
        return false;
    }

    function getHeader()
    {
        return $this->_header;
    }

    function getValues()
    {
        return $this->_values;
    }

    /**
     * Return info about field type.
     */
    function about()
    {
        return array(
            'name' => _("Table Set"),
            'params' => array(
                'values' => array('label' => _("Values"),
                                  'type'  => 'stringlist'),
                'header' => array('label' => _("Headers"),
                                  'type'  => 'stringlist')),
            );
    }

}
