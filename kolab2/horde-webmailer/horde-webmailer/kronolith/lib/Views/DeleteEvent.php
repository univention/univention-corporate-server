<?php
/**
 * The Kronolith_View_DeleteEvent:: class provides an API for viewing
 * event delete forms.
 *
 * $Horde: kronolith/lib/Views/DeleteEvent.php,v 1.3.2.1 2007-12-20 14:12:38 jan Exp $
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @since   Kronolith 2.2
 * @package Kronolith
 */
class Kronolith_View_DeleteEvent {

    var $event;

    /**
     * @param Kronolith_Event &$event
     */
    function Kronolith_View_DeleteEvent(&$event)
    {
        $this->event =& $event;
    }

    function getTitle()
    {
        if (!$this->event || is_a($this->event, 'PEAR_Error')) {
            return _("Not Found");
        }
        return sprintf(_("Delete %s"), $this->event->getTitle());
    }

    function link()
    {
        return $this->event->getDeleteUrl();
    }

    function html($active = true)
    {
        if (!$this->event || is_a($this->event, 'PEAR_Error')) {
            echo '<h3>' . _("The requested event was not found.") . '</h3>';
            return;
        }

        if ($timestamp = Util::getFormData('timestamp')) {
            $month = date('n', $timestamp);
            $year = date('Y', $timestamp);
            $day = date('j', $timestamp);
        } else {
            $month = Util::getFormData('month', date('n'));
            $day = Util::getFormData('mday', date('j'));
            $year = Util::getFormData('year', date('Y'));
        }

        $url = Util::getFormData('url');

        echo '<div id="DeleteEvent"' . ($active ? '' : ' style="display:none"') . '>';
        if (!$this->event->recurs()) {
            require KRONOLITH_TEMPLATES . '/delete/one.inc';
        } else {
            require KRONOLITH_TEMPLATES . '/delete/delete.inc';
        }
        echo '</div>';

        if ($active && $GLOBALS['browser']->hasFeature('dom')) {
            if ($this->event->hasPermission(PERMS_READ)) {
                require_once KRONOLITH_BASE . '/lib/Views/Event.php';
                $view = new Kronolith_View_Event($this->event);
                $view->html(false);
            }
            if ($this->event->hasPermission(PERMS_EDIT)) {
                require_once KRONOLITH_BASE . '/lib/Views/EditEvent.php';
                $edit = new Kronolith_View_EditEvent($this->event);
                $edit->html(false);
            }
        }
    }

    function getName()
    {
        return 'DeleteEvent';
    }

}
