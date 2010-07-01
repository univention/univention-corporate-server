<?php
/**
 * The Turba_ListView:: class provides an interface for objects that
 * visualize Turba_lists.
 *
 * $Horde: turba/lib/ListView.php,v 1.17.10.24 2009-10-26 17:34:16 jan Exp $
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @author  Jon Parise <jon@csh.rit.edu>
 * @package Turba
 */
class Turba_ListView {

    /**
     * The Turba_List object that we are visualizing.
     *
     * @var Turba_List
     */
    var $list;

    /**
     * Show/hide "mark" column in the display.
     *
     * @var boolean
     */
    var $showMark = false;

    /**
     * Show/hide "edit" column in the display.
     *
     * @var boolean
     */
    var $showEdit = false;

    /**
     * Show/hide "vcard" column in the display.
     *
     * @var boolean
     */
    var $showVcard = false;

    /**
     * Show/hide "group" column in the display.
     *
     * @var boolean
     */
    var $showGroup = false;

    /**
     * Show/hide "sort" column in the display.
     *
     * @var boolean
     */
    var $showSort = false;

    /**
     * Type of list.
     *
     * @var string
     */
    var $type;

    /**
     * The HTML renderer.
     *
     * @var Horde_UI_VarRenderer_html
     */
    var $renderer;

    /**
     * A Variables object.
     *
     * @var Variables
     */
    var $vars;

    /**
     * A list of Horde_Form_Variable objects.
     *
     * @var array
     */
    var $variables = array();

    /**
     * A dummy form object.
     *
     * @var Horde_Form
     */
    var $form = null;

    /**
     * Which columns to render
     *
     * @var array
     */
    var $columns;

    /**
     * Constructs a new Turba_ListView object.
     *
     * @param Turba_List $list  List of contacts to display.
     * @param array $controls   Which icons to display
     * @param array $columns    The list of columns to display
     */
    function Turba_ListView(&$list, $controls = null, $columns = null)
    {
        if ($controls === null) {
            $controls = array('Mark' => true,
                              'Edit' => true,
                              'Vcard' => true,
                              'Group' => true,
                              'Sort' => true);
        }
        $this->columns = $columns;

        $this->list = &$list;
        $this->setControls($controls);

        require_once 'Horde/Form.php';
        require_once 'Horde/UI/VarRenderer.php';
        require_once 'Horde/Variables.php';
        $this->renderer = Horde_UI_VarRenderer::factory('html');
        $this->vars = new Variables();
    }

    /**
     * Set which controls are shown by the display templates.
     *
     * @param array $controls
     */
    function setControls($controls)
    {
        foreach ($controls as $control => $show) {
            $key = 'show' . $control;
            $this->$key = (bool)$show;
        }
    }

    function setType($type)
    {
        $this->type = $type;
    }

    function getType()
    {
        return $this->type;
    }

    /**
     * Returns the number of Turba_Objects that are in the list. Use this to
     * hide internal implementation details from client objects.
     *
     * @return integer  The number of objects in the list.
     */
    function count()
    {
        return $this->list->count();
    }

    function display()
    {
        global $prefs, $default_source, $copymove_source_options;

        $driver = &Turba_Driver::singleton($default_source);
        $hasDelete = false;
        $hasEdit = false;
        $hasExport = false;
        if (!is_a($driver, 'PEAR_Error')) {
            if ($driver->hasPermission(PERMS_DELETE)) {
                $hasDelete = true;
            }
            if ($driver->hasPermission(PERMS_EDIT)) {
                $hasEdit = true;
            }
            if ($GLOBALS['conf']['menu']['import_export']
                && !empty($GLOBALS['cfgSources'][$default_source]['export'])) {
                $hasExport = true;
            }
        }
        list($addToList, $addToListSources) = $this->getAddSources();

        $viewurl = urldecode(Util::addParameter(
            'browse.php',
            array('key' => Util::getFormData('key'),
                  'url' => Horde::selfUrl(true, false, true))));

        if ($this->type == 'search') {
            $page = Util::getFormData('page', 0);
            $numitem = $this->count();
            $maxpage = $prefs->getValue('maxpage');
            $perpage = $prefs->getValue('perpage');

            $min = $page * $perpage;
            while ($min > $numitem) {
                $page--;
                $min = $page * $perpage;
            }

            $max = $min + $perpage;
            $start = ($page * $perpage) + 1;
            $end = min($numitem, $start + $perpage - 1);

            $listHtml = $this->getPage($numDisplayed, $min, $max);

            $crit = array();
            if ($_SESSION['turba']['search_mode'] == 'advanced') {
                $map = $driver->getCriteria();
                foreach ($map as $key => $value) {
                    if ($key != '__key') {
                        $val = Util::getFormData($key);
                        if (!empty($val)) {
                            $crit[$key] = $val;
                        }
                    }
                }
            }
            $params = array_merge($crit, array(
                'criteria' => Util::getFormData('criteria'),
                'val' => Util::getFormData('val'),
                'source' => Util::getFormData('source', $default_source)
            ));
            $viewurl = urldecode(Util::addParameter('search.php', $params));

            require_once 'Horde/UI/Pager.php';
            $vars = Variables::getDefaultVariables();
            $pager = new Horde_UI_Pager('page', $vars,
                                        array('num' => $numitem,
                                              'url' => $viewurl,
                                              'page_limit' => $maxpage,
                                              'perpage' => $perpage));

            $pagerHeader = 'numPager.inc';
        } else {
            $page = Util::getFormData('page', '*');
            if (!preg_match('/^[A-Za-z*]$/', $page)) {
                $page = '*';
            }
            if ($this->count() > $prefs->getValue('perpage')) {
                $page = Util::getFormData('page', 'A');
                if (!preg_match('/^[A-Za-z*]$/', $page)) {
                    $page = 'A';
                }
            }

            $listHtml = $this->getAlpha($numDisplayed, $page);
            $pagerHeader = 'alphaPager.inc';
        }

        if ($numDisplayed) {
            require TURBA_TEMPLATES . '/browse/actions.inc';
            require TURBA_TEMPLATES . '/list/' . $pagerHeader;
            echo $listHtml;
        } else {
            require TURBA_TEMPLATES . '/list/' . $pagerHeader;
            echo '<p><em>' . _("No matching contacts") . '</em></p>';
        }
    }

    /**
     * Renders the list contents into an HTML view.
     *
     * @param integer $numDisplayed  Ouptut parameter - the number of rows
     *                               rendered.
     * @param integer $min           Minimum number of rows to display.
     * @param integer $max           Maximum number of rows to display.
     * @return string  HTML to echo.
     */
    function getPage(&$numDisplayed, $min = 0, $max = null)
    {
        if (is_null($max)) {
            $max = $this->list->count();
        }
        return $this->_get($numDisplayed,
                           new Turba_ListView_PageFilter($min, $max));
    }

    /**
     * Renders the list contents that match $alpha into an HTML view.
     *
     * @param integer $numDisplayed  This will be set to the number of contacts
     *                               in the view.
     * @param string $alpha The letter to display.
     *
     * @return string HTML of the list.
     */
    function getAlpha(&$numDisplayed, $alpha)
    {
        return $this->_get($numDisplayed,
                           new Turba_ListView_AlphaFilter($alpha));
    }

    /**
     * Retrieves a column's name
     *
     * @param integer $i  The zero-basd index of the column
     * @return string
     */
    function getColumnName($i)
    {
        return Turba::getColumnName($i, $this->columns);
    }

    /**
     * @param integer $i  The zero-based index of the column
     */
    function getSortInfoForColumn($i)
    {
        $sortorder = Turba::getPreferredSortOrder();
        $column_name = $this->getColumnName($i);
        $i = 0;
        foreach ($sortorder as $sortfield) {
            if ($column_name == $sortfield['field']) {
                return array_merge($sortfield, array('rank' => $i));
            }
            $i++;
        }
        return null;
    }

    function getColumnSortImage($i, $title = null)
    {
        if (is_null($title)) {
            $title = _("Sort Direction");
        }
        $sortdir = $this->getColumnSortDirection($i);
        if ($this->isPrimarySortColumn($i)) {
            return Horde::img($sortdir ? 'za.png' : 'az.png', $title, null, $GLOBALS['registry']->getImageDir('horde'));
        } else {
            return Horde::img($sortdir ? 'za_secondary.png' : 'az_secondary.png', _("Sort Direction"));
        }
    }

    /**
     * Retrieves a natural language description of the sort order
     * @return string
     */
    function getSortOrderDescription()
    {
        $description = array();
        $sortorder = Turba::getPreferredSortOrder();
        foreach ($sortorder as $elt) {
            $field = $elt['field'];
            if ($field == 'lastname') {
                $field = 'name';
            }
            $description[] = $GLOBALS['attributes'][$field]['label'];
        }
        return join(', ', $description);
    }

    /**
     * @param integer $i  The zero-based index of the column
     */
    function getColumnSortDirection($i)
    {
        $result = $this->getSortInfoForColumn($i);
        if (is_null($result)) {
            return null;
        }
        return $result['ascending'] ? 0 : 1;
    }

    /**
     * Determines whether we are sorting on the specified column
     *
     * @param integer $i  The zero-based column index
     * @return boolean
     */
    function isSortColumn($i)
    {
        return !is_null($this->getSortInfoForColumn($i));
    }

    /**
     * Determines whether this is the first column to sort by
     * @param integer $i  The zero-based column index
     * @return boolean
     */
    function isPrimarySortColumn($i)
    {
        $result = $this->getSortInfoForColumn($i);
        if (is_null($result)) {
            return false;
        }
        return ($result['rank'] == 0);
    }

    function _get(&$numDisplayed, $filter)
    {
        ob_start();
        $width = floor(90 / (count($this->columns) + 1));
        @list($own_source, $own_id) = explode(';', $GLOBALS['prefs']->getValue('own_contact'));

        include TURBA_TEMPLATES . '/browse/column_headers.inc';

        $numDisplayed = 0;
        $this->list->reset();
        while ($ob = $this->list->next()) {
            if ($filter->skip($ob)) {
                continue;
            }

            include TURBA_TEMPLATES . '/browse/row.inc';
            $numDisplayed++;
        }

        include TURBA_TEMPLATES . '/browse/column_footers.inc';
        return ob_get_clean();
    }

    function getAddSources()
    {
        global $addSources;

        // Create list of lists for Add to.
        $addToList = array();
        $addToListSources = array();
        foreach ($addSources as $src => $srcConfig) {
            if (!empty($srcConfig['map']['__type'])) {
                $addToListSources[] = array('key' => '',
                                            'name' => '&nbsp;&nbsp;' . htmlspecialchars($srcConfig['title']),
                                            'source' => htmlspecialchars($src));

                $srcDriver = &Turba_Driver::singleton($src);
                $listList = $srcDriver->search(array('__type' => 'Group'),
                                               array(array('field' => 'name',
                                                           'ascending' => true)),
                                               'AND', array('name'));
                if (is_a($listList, 'PEAR_Error')) {
                    $GLOBALS['notification']->push($listList, 'horde.error');
                } else {
                    $listList->reset();
                    $currentList = Util::getFormData('key');
                    while ($listObject = $listList->next()) {
                        if ($listObject->getValue('__key') != $currentList) {
                            $addToList[] = array('name' => htmlspecialchars($listObject->getValue('name')),
                                                 'source' => htmlspecialchars($src),
                                                 'key' => htmlspecialchars($listObject->getValue('__key')));
                        }
                    }
                }
            }
        }
        if ($addToListSources) {
            if ($addToList) {
                array_unshift($addToList, '- - - - - - - - -');
            }
            $addToList = array_merge(array(_("Create a new Contact List in:")), $addToListSources, $addToList);
            $addToListSources = null;
        }

        return array($addToList, $addToListSources);
    }

}

/**
 * Skips objects whose name does not start with the specified letter
 */
class Turba_ListView_AlphaFilter {

    var $_alpha;
    var $_format;

    function Turba_ListView_AlphaFilter($alpha)
    {
        $this->_alpha = String::lower($alpha);
        $this->_format = $GLOBALS['prefs']->getValue('name_sort');
    }

    function skip(&$ob)
    {
        $name = Turba::formatName($ob, $this->_format);
        if ($this->_alpha != '*' &&
            String::lower(substr($name, 0, 1)) != $this->_alpha) {
            return true;
        }
        return false;
    }

}

/**
 * Skips objects which are not on the current page
 */
class Turba_ListView_PageFilter {

    var $_min;
    var $_max;
    var $_count = 0;

    function Turba_ListView_PageFilter($min, $max)
    {
        $this->_min = $min;
        $this->_max = $max;
    }

    function skip(&$ob)
    {
        if ($this->_count++ < $this->_min) {
            return true;
        }
        return ($this->_count > $this->_max);
    }

}
