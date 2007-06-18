<?php
/**
 * Class for auto-generating the preferences user interface and
 * processing the forms.
 *
 * $Horde: framework/Prefs/Prefs/UI.php,v 1.46 2004/05/18 19:48:24 chuck Exp $
 *
 * Copyright 2001-2004 Chuck Hagenbuch <chuck@horde.org>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 2.1
 * @package Horde_Prefs
 */
class Prefs_UI {

    /**
     * Determine whether or not a preferences group is editable.
     *
     * @access public
     *
     * @param string $group  The preferences group to check.
     *
     * @return boolean  Whether or not the group is editable.
     */
    function groupIsEditable($group)
    {
        global $prefs, $prefGroups;
        static $results;

        if (!isset($results)) {
            $results = array();
        }

        if (!isset($results[$group])) {
            if (!empty($group['url'])) {
                $results[$group] = true;
            } else {
                $results[$group] = false;
                if (isset($prefGroups[$group]['members'])) {
                    foreach ($prefGroups[$group]['members'] as $pref) {
                        if (!$prefs->isLocked($pref)) {
                            $results[$group] = true;
                            return true;
                        }
                    }
                }
            }
        }

        return $results[$group];
    }

    /**
     * Handle a preferences form submission if there is one, updating
     * any preferences which have been changed.
     *
     * @param string $group  The preferences group that was edited.
     * @param object $save   The object where the changed values are
     *                       saved. Must implement setValue(string, string).
     *
     * @return boolean  Whether preferences have been updated.
     */
    function handleForm(&$group, &$save)
    {
        global $prefs, $prefGroups, $_prefs, $notification, $registry;

        $updated = false;

        /* Run through the action handlers */
        if (Util::getFormData('actionID') == 'update_prefs') {
            if (isset($group) && Prefs_UI::groupIsEditable($group)) {
                $updated = false;

                foreach ($prefGroups[$group]['members'] as $pref) {
                    if (!$prefs->isLocked($pref) ||
                        ($_prefs[$pref]['type'] == 'special')) {
                        switch ($_prefs[$pref]['type']) {

                        /* These either aren't set or are set in other parts
                           of the UI. */
                        case 'implicit':
                        case 'link':
                            break;

                        case 'select':
                        case 'text':
                        case 'textarea':
                        case 'password':
                            $updated = $updated | $save->setValue($pref, Util::getFormData($pref));
                            break;

                        case 'enum':
                            $val = Util::getFormData($pref);
                            if (isset($_prefs[$pref]['enum'][$val])) {
                                $updated = $updated | $save->setValue($pref, $val);
                            } else {
                                $notification->push(_("An illegal value was specified."), 'horde.error');
                            }
                            break;

                        case 'multienum':
                            $vals = Util::getFormData($pref);
                            $set = array();
                            $invalid = false;
                            if (is_array($vals)) {
                                foreach ($vals as $val) {
                                    if (isset($_prefs[$pref]['enum'][$val])) {
                                        $set[] = $val;
                                    } else {
                                        $invalid = true;
                                        continue;
                                    }
                                }
                            }

                            if ($invalid) {
                                $notification->push(_("An illegal value was specified."), 'horde.error');
                            } else {
                                $updated = $updated | $save->setValue($pref, @serialize($set));
                            }
                            break;

                        case 'number':
                            $num = Util::getFormData($pref);
                            if (intval($num) != $num) {
                                $notification->push(_("This value must be a number."), 'horde.error');
                            } elseif ($num == 0) {
                                $notification->push(_("This number must be at least one."), 'horde.error');
                            } else {
                                $updated = $updated | $save->setValue($pref, $num);
                            }
                            break;

                        case 'checkbox':
                            $val = Util::getFormData($pref);
                            $updated = $updated | $save->setValue($pref, isset($val) ? 1 : 0);
                            break;

                        case 'special':
                            /* Code for special elements must be
                             * written specifically for each
                             * application. */
                            if (function_exists('handle_' . $pref)) {
                                $updated = $updated | call_user_func('handle_' . $pref, $updated);
                            }
                            break;
                        }
                    }
                }

                /* Do anything that we need to do as a result of
                 * certain preferences changing. */
                if ($prefs->isDirty('language')) {
                    NLS::setLang($prefs->getValue('language'));
                    NLS::setTextdomain($registry->getApp(), $registry->getParam('fileroot') . '/locale', NLS::getCharset());
                    String::setDefaultCharset(NLS::getCharset());
                }
                if ($prefs->isDirty('language') ||
                    $prefs->isDirty('theme') ||
                    $prefs->isDirty('menu_view')) {
                    $notification->push('if (window.parent.frames.horde_menu) window.parent.frames.horde_menu.location.reload();', 'javascript');
                }

                if ($updated) {
                    if (function_exists('prefs_callback')) {
                        prefs_callback();
                    }
                    $notification->push(_("Your options have been updated."), 'horde.message');
                    $group = null;
                }
            }
        }

        return $updated;
    }

    /**
     * Generate the UI for the preferences interface, either for a
     * specific group, or the group selection interface.
     *
     * @access public
     *
     * @param optional string $group  The group to generate the UI for.
     */
    function generateUI($group = null)
    {
        global $browser, $conf, $prefs, $prefGroups, $_prefs, $registry, $app;

        /* Show the header. */
        Prefs_UI::generateHeader($group);

        /* Assign variables to hold select lists. */
        if (!$prefs->isLocked('language')) {
            $GLOBALS['language_options'] = &$GLOBALS['nls']['languages'];
        }

        if (!empty($group) && Prefs_UI::groupIsEditable($group)) {
            foreach ($prefGroups[$group]['members'] as $pref) {
                if (!$prefs->isLocked($pref)) {
                    /* Get the help link. */
                    if (isset($_prefs[$pref]['help']) &&
                        $_prefs[$pref]['help'] &&
                        $conf['user']['online_help'] &&
                        $browser->hasFeature('javascript')) {
                        $helplink = Help::link(!empty($_prefs[$pref]['shared']) ? 'horde' : $registry->getApp(), $_prefs[$pref]['help']);
                    } else {
                        $helplink = null;
                    }

                    switch ($_prefs[$pref]['type']) {
                    case 'implicit':
                        break;

                    case 'special':
                        require $registry->getParam('templates', !empty($_prefs[$pref]['shared']) ? 'horde' : $registry->getApp()) . "/prefs/$pref.inc";
                        break;

                    default:
                        require $registry->getParam('templates', 'horde') . '/prefs/' . $_prefs[$pref]['type'] . '.inc';
                        break;
                    }
                }
            }
            require $registry->getParam('templates', 'horde') . '/prefs/end.inc';
        } else {
            $columns = array();
            if (is_array($prefGroups)) {
                foreach ($prefGroups as $group => $gvals) {
                    $col = $gvals['column'];
                    unset($gvals['column']);
                    $columns[$col][$group] = $gvals;
                }
                $span = round(100 / count($columns));
            } else {
                $span = 100;
            }

            require $registry->getParam('templates', 'horde') . '/prefs/overview.inc';
        }
    }

    /**
     * Generates the the full header of a preference screen including
     * menu and navigation bars.
     *
     * @access public
     *
     * @param optional string $group  The group to generate the header for.
     */
    function generateHeader($group = null)
    {
        global $registry, $prefGroups, $app, $menu, $perms;

        $title = _("User Options");
        require $registry->getParam('templates', $app) . '/common-header.inc';
        if (isset($menu) && is_a($menu, 'Menu')) {
            /* App has a defined menu object and can return a menu
             * array. */
            $menu = $menu->getMenu();

            /* Use the default menu template to output this menu array. */
            require $registry->getParam('templates', 'horde') . '/menu/menu.inc';
        } else {
            /* App has no menu object so is probably using a ::menu()
             * function. */
            call_user_func(array($app, 'menu'));
        }

        if (is_callable(array($app, 'status'))) {
            call_user_func(array($app, 'status'));
        } else {
            $GLOBALS['notification']->notify(array('listeners' => 'status'));
        }

        /* Get list of accessible applications. */
        $apps = array();
        foreach ($registry->applications as $application => $params) {
            if ($application == 'problem' || $application == 'logout' || $params['status'] == 'heading') {
                continue;
            }

            /* Check if the current user has permisson to see this
             * application, and if the application is active.
             * Administrators always see all applications. */
            if ((Auth::isAdmin() &&
                 ($params['status'] != 'inactive')) ||
                (($perms->exists($application) ? $perms->hasPermission($application, Auth::getAuth(), PERMS_READ) : Auth::getAuth()) &&
                 ($params['status'] == 'active' || $params['status'] == 'notoolbar'))) {
                $apps[$application] = _($params['name']);
            }
        }
        asort($apps);

        /* Show the current application and a form for switching
         * applications. */
        require $registry->getParam('templates', 'horde') . '/prefs/app.inc';

        if (!empty($group) && Prefs_UI::groupIsEditable($group)) {
            require $registry->getParam('templates', 'horde') . '/prefs/begin.inc';
        }
    }

    /**
     * Generate the content of the title bar navigation cell (previous
     * | next option group).
     *
     * @access public
     *
     * @param          string $group        Current option group.
     * @param optional string $attributes   The optional <td> attributes.
     */
    function generateNavigationCell($group, $attributes = 'class="header" align="right"')
    {
        global $prefGroups, $registry, $app;

        // Search for previous and next groups.
        $previous = null;
        $next = null;
        $last = null;
        $first = null;
        $found = false;
        $finish = false;
        foreach ($prefGroups as $pgroup => $gval) {
            if (Prefs_UI::groupIsEditable($pgroup)) {
                if (!$first) {
                    $first = $pgroup;
                }
                if (!$found) {
                    if ($pgroup == $group) {
                        $previous = $last;
                        $found = true;
                    }
                } else {
                    if (!$finish) {
                        $finish = true;
                        $next = $pgroup;
                    }
                }
                $last = $pgroup;
            }
        }
        if (!$previous) {
            $previous = $last;
        }
        if (!$next) {
            $next = $first;
        }

        /* Don't loop if there's only one group. */
        if ($next == $previous) {
            return;
        }

        echo "<td $attributes><span class='smallheader'>";
        if (!empty($prefGroups[$previous]['url'])) {
            echo Horde::link(Horde::applicationUrl($prefGroups[$previous]['url']),
                             _("Previous options"), 'menuitem');
            echo '&lt;&lt; ' . $prefGroups[$previous]['label'];
        } else {
            echo Horde::link(Util::addParameter(Horde::url($registry->getParam('webroot', 'horde') . '/services/prefs.php'), array('group' => $previous, 'app' => $app)),
                             _("Previous options"), 'menuitem');
            echo '&lt;&lt; ' . $prefGroups[$previous]['label'];
        }
        echo '</a>&nbsp;|&nbsp;';
        if (!empty($prefGroups[$next]['url'])) {
            echo Horde::link(Horde::applicationUrl($prefGroups[$next]['url']),
                             _("Next options"), 'menuitem');
            echo $prefGroups[$next]['label'] . ' &gt;&gt;';
        } else {
            echo Horde::link(Util::addParameter(Horde::url($registry->getParam('webroot', 'horde') . '/services/prefs.php'), array('group' => $next, 'app' => $app)),
                             _("Next options"), 'menuitem');
            echo $prefGroups[$next]['label'] . ' &gt;&gt;';
        }
        echo '</a></span></td>';
    }

    /**
     * Get the default application to show preferences for. Defaults
     * to 'horde'.
     */
    function getDefaultApp()
    {
        global $registry;

        $applications = $registry->listApps(null, true, PERMS_READ);
        $default = isset($applications['horde']) ? 'horde' : array_shift($applications);
        while ($default == 'logout' || $default == 'problem') {
            /* FIXME: We should probably have a better way of filtering stuff
             * like this out. */
            $default = array_shift($applications);
        }

        return $default;
    }

}
