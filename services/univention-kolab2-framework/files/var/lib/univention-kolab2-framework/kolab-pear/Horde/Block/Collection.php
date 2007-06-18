<?php
/**
 * The Horde_Block_Collection:: class provides an API to the blocks
 * (applets) framework.
 *
 * $Horde: framework/Block/Block/Collection.php,v 1.21 2004/05/30 12:31:38 jan Exp $
 *
 * Copyright 2003-2004 Mike Cochrane <mike@graftonhall.co.nz>
 * Copyright 2003-2004 Jan Schneider <jan@horde.org>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Mike Cochrane <mike@graftonhall.co.nz>
 * @author  Jan Schneider <jan@horde.org>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 3.0
 * @package Horde_Block
 */
class Horde_Block_Collection {

    /**
     * A hash storing the information about all available blocks from
     * all applications.
     *
     * @var array $_blocks
     */
    var $_blocks = array();

    /**
     * Constructor.
     */
    function Horde_Block_Collection()
    {
        if (isset($_SESSION['horde']['blocks'])) {
            $this->_blocks = $_SESSION['horde']['blocks'];
            return;
        }

        global $registry;
        require_once 'Horde/Block.php';

        foreach ($registry->listApps() as $app) {
            if (is_a($registry->pushApp($app), 'PEAR_Error')) {
                continue;
            }
            $blockdir = $registry->getParam('fileroot', $app) . '/lib/Block';
            $dh = @opendir($blockdir);
            if (is_resource($dh)) {
                while (($file = readdir($dh)) !== false) {
                    if (substr($file, -4) == '.php') {
                        $block_name = null;
                        @include_once $blockdir . '/' . $file;
                        if (!empty($block_name)) {
                            $this->_blocks[$app][substr($file, 0, -4)]['name'] = $block_name;
                        }
                    }
                }
                closedir($dh);
            }
            $registry->popApp($app);
        }

        uksort($this->_blocks,
               create_function('$a, $b',
                               'global $registry;
                                return strcasecmp($registry->getParam("name", $a), $registry->getParam("name", $b));')
               );

        $_SESSION['horde']['blocks'] = $this->_blocks;
    }

    /**
     * Returns a single instance of the Horde_Blocks class.
     *
     * @static
     *
     * @return object Horde_Blocks  The Horde_Blocks intance.
     */
    function &singleton()
    {
        static $instance;
        if (!isset($instance)) {
            $instance = &new Horde_Block_Collection();
        }
        return $instance;
    }

    /**
     * Returns a pretty printed list of all available blocks.
     *
     * @return array  A hash with block IDs as keys and application plus block
     *                block names as values.
     */
    function getBlocksList()
    {
        static $blocks = array();
        if (!empty($blocks)) {
            return $blocks;
        }

        global $registry;

        /* Get available blocks from all apps. */
        foreach ($this->_blocks as $app => $app_blocks) {
            foreach ($app_blocks as $block_id => $block) {
                $blocks[$app . ':' . $block_id] = $registry->getParam('name', $app) . ': ' . $block['name'];
            }
        }
        return $blocks;

    }

    /**
     * Returns a select widget with all available blocks.
     *
     * @param string $cur_app    The block from this application gets selected.
     * @param string $cur_block  The block with this name gets selected.
     *
     * @return string  The select tag with all available blocks.
     */
    function getBlocksWidget($cur_app = null, $cur_block = null, $onchange = false)
    {
        global $registry;

        $widget = '<select name="app"';
        if ($onchange) {
            $widget .= ' onchange="document.blockform.action.value=\'save-resume\';document.blockform.submit()"';
        }
        $widget .= ">\n";
        $blocks_list = $this->getBlocksList();
        foreach ($blocks_list as $id => $name) {
            $widget .= sprintf("<option value=\"%s\"%s>%s</option>\n",
                                   $id,
                                   ($id == $cur_app . ':' . $cur_block) ? ' selected="selected"' : '',
                                   $name);
        }
        $widget .= "</select>\n";

        return $widget;
    }

    /**
     * Returns the option type.
     */
    function getOptionType($app, $block, $param_id)
    {
        return $this->_blocks[$app][$block]['params'][$param_id]['type'];
    }

    /**
     * Returns whether the option is required or not. Defaults to true.
     */
    function getOptionRequired($app, $block, $param_id)
    {
        if (!isset($this->_blocks[$app][$block]['params'][$param_id]['required'])) {
            return true;
        } else {
            return $this->_blocks[$app][$block]['params'][$param_id]['required'];
        }
    }

    /**
     * Returns the values for an option.
     */
    function &getOptionValues($app, $block, $param_id)
    {
        return $this->_blocks[$app][$block]['params'][$param_id]['values'];
    }

    /**
     * Returns the widget necessary to configure this block.
     */
    function getOptionsWidget($app, $block, $param_id, $val = null)
    {
        $widget = '';

        $param = $this->_blocks[$app][$block]['params'][$param_id];
        switch ($param['type']) {
        case 'checkbox':
            $checked = !empty($val[$param_id]) ? ' checked="checked"' : '';
            $widget = sprintf('<input type="checkbox" name="params[%s]"%s>', $param_id, $checked);
            break;

        case 'enum':
            $widget = sprintf('<select name="params[%s]">', $param_id);
            foreach ($param['values'] as $key => $name) {
                if (String::length($name) > 30) {
                    $name = substr($name, 0, 27) . '...';
                }
                $widget .= sprintf("<option value=\"%s\"%s>%s</option>\n",
                                   $key,
                                   (isset($val[$param_id]) && $val[$param_id] == $key) ? ' selected="selected"' : '',
                                   $name);
            }

            $widget .= '</select>';
            break;

        case 'multienum':
            $widget = sprintf('<select multiple="multiple" name="params[%s][]">', $param_id);
            foreach ($param['values'] as $key => $name) {
                if (String::length($name) > 30) {
                    $name = substr($name, 0, 27) . '...';
                }
                $widget .= sprintf("<option value=\"%s\"%s>%s</option>\n",
                                   $key,
                                   (isset($val[$param_id]) && in_array($key, $val[$param_id])) ? ' selected="selected"' : '',
                                   $name);
            }

            $widget .= '</select>';
            break;

        case 'mlenum':
            // Multi-level enum.
            if (is_array($val) && isset($val['__' . $param_id])) {
                $firstval = $val['__' . $param_id];
            } else {
                $firstval = current(array_keys($param['values']));
            }
            $blockvalues = $param['values'][$firstval];
            asort($blockvalues);

            $widget = sprintf('<select name="params[__%s]" onchange="document.blockform.action.value=\'save-resume\';document.blockform.submit()">', $param_id) . "\n";
            foreach ($param['values'] as $key => $values) {
                $name = String::length($key) > 30 ? String::substr($key, 0, 27) . '...' : $key;
                $widget .= sprintf("<option value=\"%s\"%s>%s</option>\n",
                                   $key,
                                   $key == $firstval ? ' selected="selected"' : '',
                                   $name);
            }
            $widget .= "</select><br/>\n";

            $widget .= sprintf("<select name=\"params[%s]\">\n", $param_id);
            foreach ($blockvalues as $key => $name) {
                $name = (String::length($name) > 30) ? String::substr($name, 0, 27) . '...' : $name;
                $widget .= sprintf("<option value=\"%s\"%s>%s</option>\n",
                                   $key,
                                   $val[$param_id] == $key ? ' selected="selected"' : '',
                                   $name);
            }
            $widget .= "</select><br/>\n";
            break;

        case 'color':
            $val = isset($block->_params[$param_id]) ? $block->_params[$param_id] : '';
            $widget = sprintf('<input style="background-color:%s" type="text" name="params[%s]" value="%s" />', $val, $param_id, $val);
            $url  = $registry->getParam('webroot', 'horde');
            $url .= Util::addParameter('/services/images/colorpicker.php?target=params[' . $param_id . ']', 'form', 'blockform');
            $widget .= sprintf('<a href="%s" onclick="window.open(\'%s\', \'colorpicker\', \'toolbar=no,location=no,status=no,scrollbars=no,resizable=no,width=120,height=250,left=100,top=100\'); return false;" onmouseout="window.status=\'\';" onmouseover="window.status=\'%s\'; return true;" class="widget" target="colorpicker">',
                               $url, $url, _("Color Picker"));
            $widget .= Horde::img('colorpicker.gif', _("Color Picker"), 'height="16"', $registry->getParam('graphics', 'horde'));
            $widget .= '</a>';
            break;

        case 'int':
        case 'text':
            $widget = sprintf('<input type="text" name="params[%s]" value="%s" />', $param_id, empty($val) ? $param['default'] : $val[$param_id]);
            break;

        case 'error':
            $widget = '<span class="form-error">' . $val[$param_id] . '</span>';
            break;
        }

        return $widget;
    }

    /**
     * Returns the name of the specified block.
     *
     * @param string $app    An application name.
     * @param string $block  A block name.
     *
     * @return string  The name of the specified block.
     */
    function getName($app, $block)
    {
        return $this->_blocks[$app][$block]['name'];
    }

    /**
     * Returns the parameter list of the specified block.
     *
     * @param string $app    An application name.
     * @param string $block  A block name.
     *
     * @return array  An array with all paramter names.
     */
    function getParams($app, $block)
    {
        if (empty($this->_blocks[$app][$block]['params'])) {
            global $registry;
            if ($registry->hasMethod('defineBlock', $app) &&
                !is_a(($class = $registry->callByPackage($app, 'defineBlock',
                                                         array($block))), 'PEAR_Error')) {
                $this->_blocks[$app][$block]['params'] = call_user_func(array($class, 'getParams'));
            }
        }

        if (isset($this->_blocks[$app][$block]['params']) &&
            is_array($this->_blocks[$app][$block]['params'])) {
            return array_keys($this->_blocks[$app][$block]['params']);
        } else {
            return array();
        }
    }

    /**
     * Returns the (clear text) name of the specified parameter.
     *
     * @param string $app    An application name.
     * @param string $block  A block name.
     * @param string $param  A parameter name.
     *
     * @return string  The name of the specified parameter.
     */
    function getParamName($app, $block, $param)
    {
        return $this->_blocks[$app][$block]['params'][$param]['name'];
    }

    /**
     * Returns the default value of the specified parameter.
     *
     * @param string $app    An application name.
     * @param string $block  A block name.
     * @param string $param  A parameter name.
     *
     * @return string  The default value of the specified parameter or null.
     */
    function getDefaultValue($app, $block, $param)
    {
        if (isset($this->_blocks[$app][$block]['params'][$param]['default'])) {
            return $this->_blocks[$app][$block]['params'][$param]['default'];
        }
        return null;
    }

    /**
     * Returns if the specified block is customizeable by the user.
     *
     * @param string $app    An application name.
     * @param string $block  A block name.
     *
     * @return boolean  True is the block is customizeable.
     */
    function isEditable($app, $block)
    {
        return isset($this->_blocks[$app][$block]['params']) &&
            count($this->_blocks[$app][$block]['params']);
    }

}
