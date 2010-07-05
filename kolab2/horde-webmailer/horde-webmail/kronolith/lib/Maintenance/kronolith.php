<?php

require_once 'Horde/Maintenance.php';
require_once $GLOBALS['registry']->get('fileroot', 'kronolith') . '/lib/base.php';

/**
 * $Horde: kronolith/lib/Maintenance/kronolith.php,v 1.1.2.2 2009-01-06 15:24:46 jan Exp $
 *
 * The Maintenance_Kronolith class defines the maintenance operations run upon
 * login to Kronolith
 *
 * Copyright 2008-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @since   Kronolith 2.2.1
 * @package Horde_Maintenance
 */
class Maintenance_Kronolith extends Maintenance {

    /**
     * Hash holding maintenance preference names.
     *
     * @var array
     */
    var $maint_tasks = array(
        'purge_events' => MAINTENANCE_MONTHLY
    );

    /**
     * Execute all confirmed tasks.
     *
     * FIXME: This has to be overridden here since the parent's method will
     * set the global last_maintenance pref...and mess up IMP's maintenance.
     * This needs to be fixed for Horde 4.
     *
     * @access private
     */
    function _doMaintenanceTasks()
    {
        $tasks = $this->_tasklist->getList();

        foreach ($tasks as $key => $val) {
            if ($val['newpage']) {
                if ($this->_tasklist->processed()) {
                    $this->_tasklist->setNewPage($key, false);
                }
                break;
            } elseif ($val['confirmed'] ||
                      Util::getFormData($key . '_confirm')) {
                /* Perform maintenance if confirmed. */
                $mod = &$this->_loadModule($key);
                $mod->doMaintenance();
            }
            $this->_tasklist->removeTask($key);
        }

        /* If we've successfully completed every task in the list (or skipped
         * it), record now as the last time maintenance was run. */
        if (!count($this->_tasklist->getList())) {
            $GLOBALS['prefs']->setValue('last_kronolith_maintenance', time());
        }
    }



}
