<?php

$block_name = _("Menu Alarms");
$block_type = 'tree';

/**
 * $Horde: kronolith/lib/Block/tree_alarms.php,v 1.1.2.6 2008-01-02 16:50:49 chuck Exp $
 *
 * @package Horde_Block
 */
class Horde_Block_kronolith_tree_alarms extends Horde_Block {

    var $_app = 'kronolith';

    function _buildTree(&$tree, $indent = 0, $parent = null)
    {
        require_once dirname(__FILE__) . '/../base.php';

        $horde_alarm = null;
        if (!empty($GLOBALS['conf']['alarms']['driver'])) {
            require_once 'Horde/Alarm.php';
            $horde_alarm = Horde_Alarm::factory();
        }

        $alarmCount = 0;
        $alarms = Kronolith::listAlarms(new Horde_Date($_SERVER['REQUEST_TIME']),
                                        $GLOBALS['display_calendars'],
                                        true);
        if (is_a($alarms, 'PEAR_Error')) {
            return $alarms;
        }
        foreach ($alarms as $calId => $calAlarms) {
            foreach ($calAlarms as $event) {
                if ($horde_alarm && $horde_alarm->isSnoozed($event->getUID(), Auth::getAuth())) {
                    continue;
                }
                $alarmCount++;
                $tree->addNode($parent . $calId . $event->getId(),
                               $parent,
                               $event->getTitle(),
                               $indent + 1,
                               false,
                               array('icon' => 'alarm.png',
                                     'icondir' => $GLOBALS['registry']->getImageDir(),
                                     'title' => $event->getTooltip(),
                                     'url' => $event->getViewUrl()));
            }
        }

        if ($registry->get('url', $parent)) {
            $purl = $registry->get('url', $parent);
        } elseif ($registry->get('status', $parent) == 'heading' ||
                  !$registry->get('webroot')) {
            $purl = null;
        } else {
            $purl = Horde::url($registry->getInitialPage($parent));
        }
        $pnode_params = array('url' => $purl,
                              'icon' => $registry->get('icon', $parent),
                              'icondir' => '');
        $pnode_name = $registry->get('name', $parent);
        if ($alarmCount) {
            $pnode_name = '<strong>' . $pnode_name . '</strong>';
        }

        $tree->addNode($parent, $registry->get('menu_parent', $parent),
                       $pnode_name, $indent, false, $pnode_params);
    }

}
