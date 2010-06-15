<?php
/**
 * The Horde_Form_Action class provides an API for adding actions to
 * Horde_Form variables.
 *
 * $Horde: framework/Form/Form/Action.php,v 1.17 2004/03/21 18:22:19 eraserhd Exp $
 * Copyright 2002-2004 Chuck Hagenbuch <chuck@horde.org>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @version $Revision: 1.1.2.1 $
 * @package Horde_Form
 */
class Horde_Form_Action {

    var $_id;
    var $_params;
    var $_trigger = null;

    function Horde_Form_Action($params = null)
    {
        $this->_params = $params;
        $this->_id = md5(mt_rand());
    }

    function getTrigger()
    {
        return $this->_trigger;
    }

    function id()
    {
        return $this->_id;
    }

    function getActionScript($form, $renderer, $varname)
    {
        return '';
    }

    function printJavaScript()
    {
    }

    function _printJavaScriptStart()
    {
        echo '<script language="JavaScript" type="text/javascript"><!--';
    }

    function _printJavaScriptEnd()
    {
        echo '// --></script>';
    }

    function getTarget()
    {
        return isset($this->_params['target']) ? $this->_params['target'] : null;
    }

    function setValues(&$vars, $sourceVal, $index = null, $arrayVal = false)
    {
    }

    /**
     * Attempts to return a concrete Horde_Form_Action instance
     * based on $form.
     *
     * @param mixed $form    The type of concrete Horde_Form_Action subclass to return.
     *                       The code is dynamically included. If $form is an array,
     *                       then we will look in $form[0]/lib/Form/Action/ for
     *                       the subclass implementation named $form[1].php.
     * @param array $params  (optional) A hash containing any additional
     *                       configuration a form might need.
     *
     * @return object Horde_Form_Action  The concrete Horde_Form_Action reference,
     *                                   or false on an error.
     */
    function &factory($action, $params = null)
    {
        if (is_array($action)) {
            $app = $action[0];
            $action = $action[1];
        }

        $action = basename($action);
        if (empty($action) || (strcmp($action, 'none') == 0)) {
            return PEAR::raiseError('Cannot instantiate abstract class Horde_Form_Action.');
        }

        if (!empty($app)) {
            require_once $GLOBALS['registry']->getParam('fileroot', $app) . '/lib/Form/Action/' . $action . '.php';
        } elseif (@file_exists(dirname(__FILE__) . '/Action/' . $action . '.php')) {
            require_once dirname(__FILE__) . '/Action/' . $action . '.php';
        } else {
            @require_once 'Horde/Form/Action/' . $action . '.php';
        }
        $class = 'Horde_Form_Action_' . $action;
        if (class_exists($class)) {
            return $ret = &new $class($params);
        } else {
            return PEAR::raiseError('Class definition of ' . $class . ' not found.');
        }
    }

    /**
     * Attempts to return a reference to a concrete
     * Horde_Form_Action instance based on $action. It will only
     * create a new instance if no Horde_Form_Action instance with
     * the same parameters currently exists.
     *
     * This should be used if multiple types of form renderers (and,
     * thus, multiple Horde_Form_Action instances) are required.
     *
     * This method must be invoked as: $var =
     * &Horde_Form_Action::singleton()
     *
     * @param mixed $action  The type of concrete Horde_Form_Action subclass to return.
     *                       The code is dynamically included. If $action is an array,
     *                       then we will look in $action[0]/lib/Form/Action/ for
     *                       the subclass implementation named $action[1].php.
     * @param array $params  (optional) A hash containing any additional
     *                       configuration a form might need.
     *
     * @return object Horde_Form_Action  The concrete Horde_Form_Action reference,
     *                                   or false on an error.
     */
    function &singleton($action, $params = null)
    {
        static $instances;
        if (!isset($instances)) {
            $instances = array();
        }

        $signature = serialize(array($action, $params));
        if (!isset($instances[$signature])) {
            $instances[$signature] = &Horde_Form_Action::factory($action, $params);
        }

        return $instances[$signature];
    }

}
