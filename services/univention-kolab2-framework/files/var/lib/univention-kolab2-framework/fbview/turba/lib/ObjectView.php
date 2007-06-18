<?php
/**
 * The Turba_ObjectView:: class provides an interface for visualizing
 * a Turba_AbstractObject.
 *
 * $Horde: turba/lib/ObjectView.php,v 1.19 2004/04/07 14:43:52 chuck Exp $
 *
 * @author   Chuck Hagenbuch <chuck@horde.org>
 * @version  $Revision: 1.1.2.1 $
 * @since    Turba 0.0.1
 * @package  Turba
 */
class Turba_ObjectView {

	/**
     * A reference to the Turba_AbstractObject that this
     * Turba_ObjectView displays.
     * @private
     * @var	object Turba_AbstractObject $_object
     */
    var $_object;

    /**
     * The template used to display the object.
     * @private
     * @var string $_template
     */
    var $_template;

    /**
     * Do we have the creation timestamp of the object?
     * @var boolean $_created
     */
    var $_created = false;

    /**
     * Do we have the modified timestamp of the object?
     * @var boolean $_modified
     */
    var $_modified = false;

    /**
     * Constructs a new Turba_ObjectView object.
     *
     * @param object Turba_AbstractObject $object    The object to display.
     * @param string                      $template  Which template file to display this object with.
     */
    function Turba_ObjectView(&$object, $template = null)
    {
        $this->_object = &$object;
        $this->_template = $template;
    }

    /**
     * Set up the Horde_Form for the current object's attributes.
     *
     * @param object Horde_Form &$form  The form to set variables on.
     */
    function setupForm(&$form)
    {
        require TURBA_BASE . '/config/attributes.php';

        $fields = array_keys($this->_object->source->getCriteria());

        // Run through once to see what form actions, if any, we need
        // to set up.
        $actions = array();
        $map = $this->_object->source->map;
        foreach ($fields as $field) {
            if (is_array($map[$field])) {
                foreach ($map[$field]['fields'] as $action_field) {
                    if (!isset($actions[$action_field])) {
                        $actions[$action_field] = array();
                    }
                    $actions[$action_field]['fields'] = $map[$field]['fields'];
                    $actions[$action_field]['format'] = $map[$field]['format'];
                    $actions[$action_field]['target'] = $field;
                }
            }
        }

        // Now run through and add the form variables.
        foreach ($fields as $field) {
            if (!isset($attributes[$field])) {
                continue;
            }

            $attribute = $attributes[$field];
            $params = isset($attribute['params']) ? $attribute['params'] : array();
            $desc = isset($attribute['desc']) ? $attribute['desc'] : null;

            if (is_array($map[$field])) {
                $v = &$form->addVariable($attribute['label'], 'object[' . $field . ']', $attribute['type'], false, false, $desc, $params);
                $v->disable();
            } else {
                $readonly = isset($attribute['readonly']) ? $attribute['readonly'] : null;
                $v = &$form->addVariable($attribute['label'], 'object[' . $field . ']', $attribute['type'], $attribute['required'], $readonly, $desc, $params);

                if (!empty($actions[$field])) {
                    require_once 'Horde/Form/Action.php';
                    $actionfields = array();
                    foreach ($actions[$field]['fields'] as $f) {
                        $actionfields[] = 'object[' . $f . ']';
                    }
                    $a = &Horde_Form_Action::factory('updatefield',
                                                     array('format' => $actions[$field]['format'],
                                                           'target' => 'object[' . $actions[$field]['target'] . ']',
                                                           'fields' => $actionfields));
                    $v->setAction($a);
                }
            }
        }

        if ($this->_created) {
            $v = &$form->addVariable(_("Created"), 'object[__created]', 'text', false, false);
            $v->disable();
        }

        if ($this->_modified) {
            $v = &$form->addVariable(_("Last Modified"), 'object[__modified]', 'text', false, false);
            $v->disable();
        }
    }

    /**
     * Renders the object into an HTML view.
     */
    function display()
    {
        require TURBA_BASE . '/config/attributes.php';
        $fields = $this->_object->source->getCriteria();
        require $this->_template;
    }

    /**
     * Set $attribute to $value.
     *
     * @param string $attribute  The attribute to set.
     * @param mixed  $value      The value for $attribute.
     */
    function set($attribute, $value)
    {
        $attribute = '_' . $attribute;
        $this->$attribute = $value;
    }

}
