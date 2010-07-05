<?php
/**
 * Horde_Form for editing notepads.
 *
 * $Horde: mnemo/lib/Forms/EditNotepad.php,v 1.2.2.1 2007-12-20 14:17:46 jan Exp $
 *
 * See the enclosed file LICENSE for license information (ASL). If you
 * did not receive this file, see http://www.horde.org/licenses/asl.php.
 *
 * @package Mnemo
 */

/** Variables */
require_once 'Horde/Variables.php';

/** Horde_Form */
require_once 'Horde/Form.php';

/** Horde_Form_Renderer */
require_once 'Horde/Form/Renderer.php';

/**
 * The Mnemo_EditNotepadForm class provides the form for
 * editing a notepad.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @since   Mnemo 2.2
 * @package Mnemo
 */
class Mnemo_EditNotepadForm extends Horde_Form {

    /**
     * Notepad being edited
     */
    var $_notepad;

    function Mnemo_EditNotepadForm(&$vars, &$notepad)
    {
        $this->_notepad = &$notepad;
        parent::Horde_Form($vars, sprintf(_("Edit %s"), $notepad->get('name')));

        $this->addHidden('', 'n', 'text', true);
        if ($this->_notepad->get('owner') != Auth::getAuth()) {
            $this->addVariable(_("Name"), 'name', 'text', false, true);
            $this->addVariable(_("Description"), 'description', 'longtext', false, true);
        } else {
            $this->addVariable(_("Name"), 'name', 'text', true);
            $this->addVariable(_("Description"), 'description', 'longtext', false, false, null, array(4, 60));
        }

        $this->setButtons(array(_("Save")));
    }

    function activeSyncSegment($devices)
    {
        $this->addHidden('', 'activesync_devices', 'text');
        $this->addVariable('', '', 'spacer');
        $this->addVariable(_("Synchronization options for ActiveSync devices"), '', 'header');
        foreach ($devices as $id => $config) {
            $this->addVariable(sprintf("Device \"%s\"", $id), 'activesync_' . $id, 'radio', false, false, null, 
                           array(array(_("does not synchronize with this notepad"), _("synchronizes with this notepad"))));
        }
    }

    function execute()
    {
        if ($this->_notepad->get('owner') == Auth::getAuth()) {
            $this->_notepad->set('name', $this->_vars->get('name'));
        }
        $this->_notepad->set('desc', $this->_vars->get('description'));

        if ($this->_vars->get('activesync_devices', '')) {
            $params = array();
            $ids = explode('|', $this->_vars->get('activesync_devices', ''));
            foreach ($ids as $id) {
                $sync = (int) $this->_vars->get('activesync_' . $id, 0);
                if ($sync === 0 || $sync === 1 || $sync === 2) {
                    $params['activesync']['FOLDER'][$id]['S'] = $sync;
                }
            }
            $this->_notepad->set('params', serialize($params));
        }

        $result = $this->_notepad->save();
        if (is_a($result, 'PEAR_Error')) {
            return PEAR::raiseError(sprintf(_("Unable to save notepad \"%s\": %s"), $id, $result->getMessage()));
        }
        return true;
    }

}
