<?php
/**
 * The Kronolith_View_Event:: class provides an API for viewing events.
 *
 * $Horde: kronolith/lib/Views/Event.php,v 1.7.2.3 2008-11-10 05:15:45 chuck Exp $
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @since   Kronolith 2.2
 * @package Kronolith
 */
class Kronolith_View_Event {

    var $event;

    /**
     * @param Kronolith_Event &$event
     */
    function Kronolith_View_Event(&$event)
    {
        $this->event = &$event;
    }

    function getTitle()
    {
        if (!$this->event || is_a($this->event, 'PEAR_Error')) {
            return _("Not Found");
        }
        return $this->event->getTitle();
    }

    function link()
    {
        return $this->event->getViewUrl();
    }

    function html($active = true)
    {
        global $conf, $prefs;

        if (!$this->event || is_a($this->event, 'PEAR_Error')) {
            echo '<h3>' . _("The requested event was not found.") . '</h3>';
            return;
        }

        require_once 'Horde/MIME.php';
        require_once 'Horde/Text.php';
        require_once 'Horde/Text/Filter.php';

        $createdby = '';
        $modifiedby = '';
        $userId = Auth::getAuth();
        if ($this->event->getUID()) {
            /* Get the event's history. */
            $history = &Horde_History::singleton();
            $log = $history->getHistory('kronolith:' . $this->event->getCalendar() . ':' .
                                        $this->event->getUID());
            if ($log && !is_a($log, 'PEAR_Error')) {
                foreach ($log->getData() as $entry) {
                    switch ($entry['action']) {
                    case 'add':
                        $created = $entry['ts'];
                        if ($userId != $entry['who']) {
                            $createdby = sprintf(_("by %s"), Kronolith::getUserName($entry['who']));
                        } else {
                            $createdby = _("by me");
                        }
                        break;

                    case 'modify':
                        $modified = $entry['ts'];
                        if ($userId != $entry['who']) {
                            $modifiedby = sprintf(_("by %s"), Kronolith::getUserName($entry['who']));
                        } else {
                            $modifiedby = _("by me");
                        }
                        break;
                    }
                }
            }
        }

        $creatorId = $this->event->getCreatorId();
        $category = $this->event->getCategory();
        $description = $this->event->getDescription();
        $location = $this->event->getLocation();
        $private = $this->event->isPrivate() && $creatorId != Auth::getAuth();
        $owner = Kronolith::getUserName($creatorId);
        $status = Kronolith::statusToString($this->event->getStatus());
        $attendees = $this->event->getAttendees();

        if ($conf['metadata']['keywords']) {
            include KRONOLITH_BASE . '/config/keywords.php';
            $keyword_list = array();
            foreach ($keywords as $cat => $list) {
                $sub_list = array();
                foreach ($list as $entry) {
                    if ($this->event->hasKeyword($entry)) {
                        $sub_list[] = htmlspecialchars($entry);
                    }
                }
                if (count($sub_list)) {
                    $keyword_list[$cat] = $sub_list;
                }
            }
        }

        if ($timestamp = (int)Util::getFormData('timestamp')) {
            $month = date('n', $timestamp);
            $year = date('Y', $timestamp);
        } else {
            $month = (int)Util::getFormData('month', date('n'));
            $year = (int)Util::getFormData('year', date('Y'));
        }

        echo '<div id="Event"' . ($active ? '' : ' style="display:none"') . '>';
        require KRONOLITH_TEMPLATES . '/view/view.inc';
        echo '</div>';

        if ($active && $GLOBALS['browser']->hasFeature('dom')) {
            if ($this->event->hasPermission(PERMS_EDIT)) {
                require_once KRONOLITH_BASE . '/lib/Views/EditEvent.php';
                $edit = new Kronolith_View_EditEvent($this->event);
                $edit->html(false);
            }
            if ($this->event->hasPermission(PERMS_DELETE)) {
                require_once KRONOLITH_BASE . '/lib/Views/DeleteEvent.php';
                $delete = new Kronolith_View_DeleteEvent($this->event);
                $delete->html(false);
            }
        }
    }

    function getName()
    {
        return 'Event';
    }

}
