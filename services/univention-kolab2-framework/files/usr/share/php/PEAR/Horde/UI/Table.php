<?php

require_once dirname(__FILE__) . '/Widget.php';

/**
 * The Horde_UI_Table:: class displays and allows manipulation of tabular
 * data.
 *
 * $Horde: framework/UI/UI/Table.php,v 1.1 2004/05/02 21:25:56 eraserhd Exp $
 *
 * Copyright 2001 Robert E. Coyle <robertecoyle@hotmail.com>
 *
 * See the enclosed file LICENSE for license information (BSD). If you
 * did not receive this file, see http://www.horde.org/licenses/bsdl.php.
 *
 * @version $Revision: 1.1.2.1 $
 * @since   Horde_UI 0.0.1
 * @package Horde_UI
 */
class Horde_UI_Table extends Horde_UI_Widget {

    /**
     * Data loaded from the getTableMetaData API.
     *
     * @access private
     * @var array $_metaData
     */
    var $_metaData = null;

    var $_formVars = array();

    function getMetaData()
    {
        global $registry;
        if (is_null($this->_metaData)) {
            list($app, $name) = explode('/', $this->_config['name']);
            $args = array($name, $this->_config['params']);
            $this->_metaData = $registry->callByPackage($app,
                                                        'getTableMetaData',
                                                        $args);

            // We need to make vars for the columns.
            foreach ($this->_metaData['columns'] as $col) {
                $typename = isset($col['type']) ? $col['type'] : 'text';
                $params = isset($col['params']) ? $col['params'] : array();
                $type = &Horde_Form::getType($typename, $params);

                $var = &new Horde_Form_Variable($col['title'], $col['name'],
                                                $type, false, true, '');
                $this->_formVars[$col['name']] = &$var;
            }
        }
        return $this->_metaData;
    }

    function _getData($start, $end)
    {
        global $registry;
        list($app, $name) = explode('/', $this->_config['name']);
        $args = array($name, $this->_config['params'], $start, $end);
        return $registry->callByPackage($app, 'getTableData', $args);
    }

    function getColumnCount()
    {
        $this->getMetaData();
        return count($this->_metaData['columns']);
    }

    /**
     * Render the tabs.
     */
    function render()
    {
        global $registry;

        $this->getMetaData();

        require_once dirname(__FILE__) . '/VarRenderer.php';
        $varRenderer = &Horde_UI_VarRenderer::singleton('html');

        $html = '<table width="100%" cellspacing="1" cellpadding="0" border="0" class="item"><tr><td align="left" class="header" colspan="' .
                $this->getColumnCount() . '">';

        // Table title.
        if (isset($this->_config['title'])) {
            $title = $this->_config['title'];
        } else {
            $title = _("Table");
        }
        $html .= $title;

        /*
        //
        // Export icon.  We store the parameters in the session so that smart
        // users can't hack it (in Hermes, you could make it show other
        // people's time, for example).
        //
        $id = $this->_config['name'] . ':' . $this->_name;
        $_SESSION['horde']['tables'][$id] = $this->_config;
        $exportlink = Horde::url($registry->getParam('webroot', 'horde') .
                                 '/services/table/export.php');
        $exportlink = Util::addParameter($exportlink, array('id' => $id));

        $html .= ' &nbsp;' . Horde::link($exportlink, _("Export Data")) .
                 Horde::img('data.gif', _("Export Data"), 'hspace="2"',
                            $registry->getParam('graphics', 'horde')) .
                 '</a>';
        */

        // Column titles.
        $html .= '</td></tr><tr class="item">';
        foreach ($this->_metaData['columns'] as $col) {
            $html .= '<td><b>' . $col['title'] . '</b></td>';
        }
        $html .= '</tr>';

        // Display data.
        $data = $this->_getData(0, $this->_metaData['rows']);
        if (empty($data)) {
            $html .= '<tr><td colspan="' . $this->getColumnCount() . '"><em>' .
                     '&nbsp; &nbsp; ' .
                     _("(There are no rows to display.)") . '</em></td></tr>';
        } else {
            /* This Variables:: is populated for each table row so that we
             * can use the Horde_UI_VarRenderer:: */
            $vars = &new Variables();
            $form = null;
            foreach ($data as $row) {
                $html .= '<tr class="text" ' .
                         'onmouseover="className=\'text-hi\';" ' .
                         'onmouseout="className=\'text\';">';
                foreach ($row as $key => $value) {
                    $vars->set($key, $value);
                }
                foreach ($this->_metaData['columns'] as $col) {
                    $value = null;
                    if (isset($row[$col['name']])) {
                        $value = $row[$col['name']];
                    }
                    $align = '';
                    if (isset($col['align'])) {
                        $align = ' align="' . htmlspecialchars($col['align']) .
                                 '"';
                    }
                    $html .= "<td$align>";
                    if (!empty($col['nobr'])) {
                        $html .= '<nobr>';
                    }
                    $html .= $varRenderer->render($form, $this->_formVars[$col['name']], $vars);
                    if (!empty($col['nobr'])) {
                        $html .= '</nobr>';
                    }
                    $html .= '</td>';
                }
                $html .= '</tr>';
            }
        }

        $html .= '</table>';
        return $html;
    }

}
