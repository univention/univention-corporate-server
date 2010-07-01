<?php
/**
 * The Kronolith_View_EditEvent:: class provides an API for viewing
 * event edit forms.
 *
 * $Horde: kronolith/lib/Views/EditEvent.php,v 1.9.2.2 2008-03-17 09:25:44 jan Exp $
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @since   Kronolith 2.2
 * @package Kronolith
 */
class Kronolith_View_EditEvent {

    var $event;

    /**
     * @param Kronolith_Event &$event
     */
    function Kronolith_View_EditEvent(&$event)
    {
        $this->event = &$event;
    }

    function getTitle()
    {
        if (!$this->event || is_a($this->event, 'PEAR_Error')) {
            return _("Not Found");
        }
        return sprintf(_("Edit %s"), $this->event->getTitle());
    }

    function link()
    {
        return $this->event->getEditUrl();
    }

    function html($active = true)
    {
        require_once 'Horde/Identity.php';
        $identity = &Identity::singleton();

        if (!$this->event || is_a($this->event, 'PEAR_Error')) {
            echo '<h3>' . _("The requested event was not found.") . '</h3>';
            return;
        }

        if ($this->event->isRemote()) {
            $calendar_id = Kronolith::getDefaultCalendar(PERMS_EDIT);
        } else {
            $calendar_id = $this->event->getCalendar();
        }
        if (!$this->event->hasPermission(PERMS_EDIT) &&
            !is_a($share = &$this->event->getShare(), 'PEAR_Error')) {
            $calendar_id .= ':' . $share->get('owner');
        }
        $_SESSION['kronolith']['attendees'] = $this->event->getAttendees();

        if ($timestamp = Util::getFormData('timestamp')) {
            $month = date('n', $timestamp);
            $year = date('Y', $timestamp);
        } else {
            $month = Util::getFormData('month', date('n'));
            $year = Util::getFormData('year', date('Y'));
        }

        $url = Util::getFormData('url');
        $perms = PERMS_EDIT;
        if ($this->event->getCreatorId() == Auth::getAuth()) {
            $perms |= PERMS_DELEGATE;
        }
        $calendars = Kronolith::listCalendars(false, $perms);

        $buttons = array();
        if (($this->event->isRemote() ||
             !$this->event->hasPermission(PERMS_EDIT)) &&
            (!empty($GLOBALS['conf']['hooks']['permsdenied']) ||
             Kronolith::hasPermission('max_events') === true ||
             Kronolith::hasPermission('max_events') > Kronolith::countEvents())) {
            $buttons[] = '<input type="submit" class="button" name="saveAsNew" value="' . _("Save As New") . '" onclick="return checkCategory();" />';
        } else {
            if (!$this->event->isRemote()) {
                $buttons[] = '<input type="submit" class="button" name="save" value="' . _("Save Event") . '" onclick="return checkCategory();" />';
            }
            if ($this->event->isInitialized()) {
                if (!$this->event->recurs() &&
                    (!empty($conf['hooks']['permsdenied']) ||
                     Kronolith::hasPermission('max_events') === true ||
                     Kronolith::hasPermission('max_events') > Kronolith::countEvents())) {
                    $buttons[] = '<input type="submit" class="button" name="saveAsNew" value="' . _("Save As New") . '" onclick="return checkCategory();" />';
                }
            }
        }

        if (isset($url)) {
            $cancelurl = $url;
        } else {
            $cancelurl = Util::addParameter('month.php', array('month' => $month,
                                                               'year', $year));
            $cancelurl = Horde::applicationUrl($cancelurl, true);
        }

        $event = &$this->event;

        echo '<div id="EditEvent"' . ($active ? '' : ' style="display:none"') . '>';
        require KRONOLITH_TEMPLATES . '/edit/javascript.inc';
        require KRONOLITH_TEMPLATES . '/edit/edit.inc';
        echo '</div>';

        if ($active && $GLOBALS['browser']->hasFeature('dom')) {
            if ($this->event->hasPermission(PERMS_READ)) {
                require_once KRONOLITH_BASE . '/lib/Views/Event.php';
                $view = new Kronolith_View_Event($this->event);
                $view->html(false);
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
        return 'EditEvent';
    }

}
