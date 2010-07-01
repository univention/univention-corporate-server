<?php
/**
 * The Horde_Editor_xinha:: class provides access to the Xinha editor for use
 * in the Horde Framework.
 *
 * Xinha website: http://xinha.python-hosting.com/
 *
 * $Horde: framework/Editor/Editor/xinha.php,v 1.27.2.5 2009-01-06 15:23:03 jan Exp $
 *
 * Copyright 2003-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Nuno Loureiro <nuno@co.sapo.pt>
 * @author  Jan Schneider <jan@horde.org>
 * @author  Roel Gloudemans <roel@gloudemans.info>
 * @since   Horde 3.2
 * @package Horde_Editor
 */
class Horde_Editor_xinha extends Horde_Editor {

    /**
     * Constructor.
     *
     * @param array $params  The following configuration parameters:
     * <pre>
     * 'config' - An array of additional config items. Values will be quoted
     *            unless they begin with the string '@raw@' in which case
     *            they will be output as-is.
     * 'hidebuttons' - A list of buttons to hide.
     * 'id' - The ID of the text area to turn into an editor.
     * 'lang' - The language to use. (Default: en)
     * 'loadnotify' - Display notification graphic when loading (Default: no)
     * 'no_autoload' - Don't load xinha by default on pageload.
     * 'no_notify' - Don't output JS code via notification library. Code will
     *               be stored for access via getJS().
     * 'noplugins' - A list of plugins to specifically never load.
     * 'plugins' - Any plugins to load in addition to the plugins_stored in
     *             'editor_plugins'.
     * 'relativelinks' - TODO
     * 'textarea' - Turn all textareas on page into editors? (Default: no)
     * </pre>
     */
    function Horde_Editor_xinha($params = array())
    {
        $language = 'en';
        if (!empty($params['lang'])) {
            $language = $params['lang'];
        } elseif (isset($GLOBALS['language'])) {
            $language = explode('_', $GLOBALS['language']);
            if (count($language) > 1) {
                $country = String::lower($language[1]);
                if ($country == $language[0]) {
                    $language = $language[0];
                } else {
                    $language = $language[0] . '_' . $country;
                }
            } else {
                $language = $language[0];
            }
        }

        if (($language != 'pt_br') &&
            ($pos = strpos($language, '_'))) {
            $language = substr($language, 0, $pos);
        }

        $xinha_path = $GLOBALS['registry']->get('webroot', 'horde') . '/services/editor/xinha/';

        $js = 'var _editor_url = \'' . $xinha_path . '\',' .
              '_editor_lang = \'' . $language . '\',' .
              '_editors,' .
              'xinha_init = function() { ';

        // Loading plugins.
        $plugins = @unserialize($GLOBALS['prefs']->getValue('editor_plugins'));
        if (!$plugins) {
            $plugins = array();
        }
        $key = array_search('AnselImage', $plugins);
        if (($key !== false) &&
            !$GLOBALS['registry']->hasMethod('images/listGalleries')) {
            unset($plugins[$key]);
        }
        if (!empty($params['plugins'])) {
            $plugins += $params['plugins'];
        }
        if (!empty($params['noplugins'])) {
            $plugins = array_diff($plugins, $params['noplugins']);
        }

        $js .= 'var xinha_plugins = ';
        if (empty($plugins)) {
            $js .= '[];';
        } else {
            $js .= '[\'' . implode('\',\'', array_unique($plugins)) . '\'];';
        }

        $js .= 'if (!Xinha.loadPlugins(xinha_plugins, xinha_init)) return; ';

        $js .= 'var xinha_editors = ';
        if (!empty($params['id'])) {
            $js .= '[\'' . $params['id'] . '\'];';
        } elseif (!empty($params['textarea'])) {
            $js .= 'document.getElementsByTagName(\'TEXTAREA\');';
        } else {
            $js .= '[];';
        }

        $js .= 'var xinha_config = new Xinha.Config();' .
               'xinha_config.debug = false;';

        if (!empty($params['hidebuttons'])) {
            $js .= 'xinha_config.hideSomeButtons(\' ' . implode(' ', $params['hidebuttons']) . ' \');';
        }

        if (!empty($params['loadnotify'])) {
            $params['config']['showLoading'] = true;
        }

        if (!empty($params['relativelinks'])) {
            $myserver = Horde::url('', true);
            $params['config'] = array_merge($params['config'], array('stripBaseHref' => true, 'stripSelfNamedAnchors' => true, 'baseHref' => substr($myserver, 0, strpos($myserver, '/', 8))));
        }

        if (!empty($params['config'])) {
            foreach ($params['config'] as $config => $value) {
                $js .= 'xinha_config.' . $config . ' = ';
                if (is_bool($value)) {
                    $js .= ($value) ? 'true;' : 'false;';
                } elseif (strpos($value, '@raw@') === 0) {
                    $js .= substr($value, 5) . ';';
                } else {
                    $js .= '\'' . addslashes($value) . '\';';
                }
            }
        }

        $js .= '_editors = Xinha.makeEditors(xinha_editors, xinha_config, xinha_plugins);' .
               'Xinha.startEditors(_editors); };';

        if (empty($params['no_autoload'])) {
            Horde::addScriptFile('prototype.js', 'horde', true);
            $js .= 'Event.observe(window, \'load\', xinha_init);';
        }

        if (!empty($params['no_notify'])) {
            $this->_js = '<script type="text/javascript">' . $js . '</script><script type="text/javascript" src="' . $xinha_path . 'XinhaCore.js"></script>';
        } else {
            $GLOBALS['notification']->push($js, 'javascript');
            $GLOBALS['notification']->push($xinha_path . 'XinhaCore.js', 'javascript-file');
        }
    }

}
