<?php
/**
 * @package Turba
 *
 * $Horde: turba/lib/Forms/Contact.php,v 1.3.2.4 2008-12-29 07:58:45 wrobel Exp $
 */

/** Horde_Form */
require_once 'Horde/Form.php';

/** Horde_Form_Action */
require_once 'Horde/Form/Action.php';

/**
 * @package Turba
 */
class Turba_ContactForm extends Horde_Form {

    function Turba_ContactForm(&$vars, &$contact)
    {
        global $conf, $notification;

        parent::Horde_Form($vars, '', 'Turba_View_Contact');

        /* Get the values through the Turba_Object class. */
        $object = array();
        foreach ($contact->driver->getCriteria() as $info_key => $info_val) {
            $object[$info_key] = $contact->getValue($info_key);
        }
        $vars->set('object', $object);

        $this->_addFields($contact);

        /* List files. */
        $v_params = Horde::getVFSConfig('documents');
        if ($v_params['type'] != 'none') {
            $files = $contact->listFiles();
            if (is_a($files, 'PEAR_Error')) {
                $notification->push($files, 'horde.error');
            } else {
                $this->addVariable(_("Files"), '__vfs', 'html', false);
                $vars->set('__vfs', implode('<br />', array_map(array($contact, 'vfsEditUrl'), $files)));
            }
        }
    }

    /**
     * Set up the Horde_Form fields for $contact's attributes.
     */
    function _addFields($contact)
    {
        global $attributes;

        // Run through once to see what form actions, if any, we need
        // to set up.
        $actions = array();
        $map = $contact->driver->map;
        $fields = array_keys($contact->driver->getCriteria());
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
        $tabs = $contact->driver->tabs;
        if (!count($tabs)) {
            $tabs = array('' => $fields);
        }
        foreach ($tabs as $tab => $tab_fields) {
            if (!empty($tab)) {
                $this->setSection($tab, $tab);
            }
            foreach ($tab_fields as $field) {
                if (!in_array($field, $fields) ||
                    !isset($attributes[$field])) {
                    continue;
                }

                $attribute = $attributes[$field];
                $params = isset($attribute['params']) ? $attribute['params'] : array();
                $desc = isset($attribute['desc']) ? $attribute['desc'] : null;

                if (is_array($map[$field])) {
                    $v = &$this->addVariable($attribute['label'], 'object[' . $field . ']', $attribute['type'], false, false, $desc, $params);
                    $v->disable();
                } else {
                    $readonly = isset($attribute['readonly']) ? $attribute['readonly'] : null;
                    $v = &$this->addVariable($attribute['label'], 'object[' . $field . ']', $attribute['type'], $attribute['required'], $readonly, $desc, $params);

                    if (!empty($actions[$field])) {
                        $actionfields = array();
                        foreach ($actions[$field]['fields'] as $f) {
                            $actionfields[] = 'object[' . $f . ']';
                        }
                        $a = Horde_Form_Action::factory('updatefield',
                                                        array('format' => $actions[$field]['format'],
                                                              'target' => 'object[' . $actions[$field]['target'] . ']',
                                                              'fields' => $actionfields));
                        $v->setAction($a);
                    }
                }

                if (isset($attribute['default'])) {
                    $v->setDefault($attribute['default']);
                }
            }
        }
    }

}
