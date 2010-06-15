<?php

require_once 'Horde/DataTree.php';

/**
 * Horde_Links API.
 *
 * We refer to type if we mean the (string) link types name or
 * identifier. We refer to definition if we mean the (hash) with link
 * properties. In the _definitions hash the definitions are identified
 * by the types.
 *
 * Copyright 2003-2004, Jeroen Huinink <j.huinink@wanadoo.nl>
 * Copyright 2003-2004, Chuck Hagenbuch <chuck@horde.org>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * $Horde: framework/Links/Links.php,v 1.37 2004/04/07 14:43:09 chuck Exp $
 *
 * @author  Jeroen Huinink <j.huinink@wanadoo.nl>
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 3.0
 * @package Horde_Links
 */
class Horde_Links {

    /**
     * Name of the application from which the links are created.
     *
     * @access private
     *
     * @var string $_from_application
     */
    var $_from_application;

    /**
     * Pointer to a datatree instance to manage the links.
     *
     * @var object DataTree $_datatree
     */
    var $_datatree;

    /**
     * The subclass of DataTreeObject to instantiate links as.
     *
     * @var string $_linkObject
     */
    var $_linkObject = 'DataTreeObject_Link';

    /**
     * Hash with available link definitions
     *
     * @access private
     *
     * @var string $_definitions;
     */
    var $_definitions = array();

    /**
     * Array to hold retrieved links
     *
     * @access private
     *
     * @var string $_links;
     *
     */
    var $_links = array();

    /**
     * Unique name for the link
     *
     * @var string $name
     */
    var $_name;

    /**
     * Constructor.
     *
     * @access public
     *
     * @param string $from_application   The 'provides' value for the links.
     */
    function Horde_Links($from_application = false)
    {
        global $conf;

        if (!isset($conf['datatree']['driver'])) {
            Horde::fatal('You must configure a DataTree backend to use Links.');
        }

        $driver = $conf['datatree']['driver'];
        $this->_datatree = &DataTree::singleton($driver,
                                                array_merge(Horde::getDriverConfig('datatree', $driver),
                                                            array('group' => 'horde.links')));

        global $registry;
        if ($from_application) {
            $this->_from_application = $from_application;
            $definitions = $registry->getParam('links');
            if (is_array($definitions) && count($definitions)) {
                foreach ($definitions as $type => $definition) {
                    $description = $definition['description'];
                    $this->_definitions[$this->_from_application . '/' . $type]['provider'] = $definition['provider'];
                    $this->_definitions[$this->_from_application . '/' . $type]['description'] = gettext($description);
                    $this->_definitions[$this->_from_application . '/' . $type]['readonly'] = (isset($definition['readonly']) && $definition['readonly']);
                    $this->_definitions[$this->_from_application . '/' . $type]['show'] = (isset($definition['show'])) ? $definition['show'] : true;
                }
            } else {
                $this->_definitions = array();
            }

            $provides = $registry->getParam('provides');
            foreach ($registry->listApps() as $app) {
                $definitions = $registry->getParam('links', $app);
                if (is_array($definitions) && count($definitions)) {
                    foreach ($definitions as $type => $definition) {
                        if ($definition['provider'] == $provides) {
                            if (!empty($definition['reverse'])) {
                                $reverse_provider = $registry->getParam('provides', $app);
                                if (isset($definition['reverse']['description'])) {
                                    $reverse_description = $definition['reverse']['description'];
                                } else {
                                    $reverse_description = $definition['description'];
                                }
                                $this->_definitions[$reverse_provider . '/' . $type . '/reverse'] = array(
                                    'provider' => $reverse_provider,
                                    'description' => $reverse_description,
                                    'type' => $type,
                                    'readonly' => (isset($definition['reverse']['readonly']) && $definition['reverse']['readonly']),
                                    'show' => (isset($definition['reverse']['show']) ? $definition['reverse']['show'] : true),
                                );
                            }
                        }
                    }
                }
            }
        }
    }

    /**
     * This function returns the list of link definitions.
     *
     * @access public
     *
     * @return array  The list of link definitions.
     */
    function listLinkTypes()
    {
        return $this->_definitions;
    }

    /**
     * This function returns a list of links for the specified
     * type and the specified from_parameters.
     *
     * @access public
     *
     * @param array $link_criteria  Hash with the following structure:
     *                                $link_criteria[$name][$key] = $value
     *                              where $key is one of: 'link_param',
     *                              'link_to_param' or 'link_from_param'
     *                              and $key and $value are an arbitrary
     *                              link properties pair.
     *
     * @return array  The list of links.
     */
    function listLinks($link_criteria)
    {
        // Get links from the DataTree driver.
        $links = $this->_datatree->getByAttributes($this->_buildCriteria($link_criteria),
                                                   '-1', true, false);
        $attributes = array();

        if (count($links)) {
            // Get all available data for these links.
            $cids = array();
            foreach ($links as $id => $name) {
                $cids[] = $id;
                $attributes[$id]['name'] = $name;
            }
            $link_results = $this->_datatree->getAttributes($cids);
            foreach ($link_results as $id => $attr) {
                foreach ($attr as $key => $vals) {
                    $attribute_key = $vals['key'];
                    $attribute_value = $vals['value'];
                    $attribute_name = $vals['name'];
                    $attributes[$id][$attribute_name][$attribute_key] = $attribute_value;
                }
            }
        }

        return $attributes;
    }

    /**
     * This function provides the general (shared) user interface for
     * links.
     *
     * @access public
     *
     * @param array $link_data
     *
     * @return array  The list of links.
     */
    function viewLinks($link_data)
    {
        global $registry;

        if (!isset($link_data['link_params']['from_application'])) {
            $link_data['link_params']['from_application'] = $this->_from_application;
        }

        foreach ($this->_definitions as $type => $definition) {
            $link_data['link_params']['link_type'] = $type;
            $app = $this->_definitions[$type]['provider'];

            if ($this->_definitions[$type]['show'] &&
                ($registry->hasMethod($app . '/addLink') ||
                 $registry->hasMethod($app . '/getLinkDescription'))) {
                $reverse = (substr($type, -8) == '/reverse') ? '/reverse' : '';
                include $registry->getParam('templates', 'horde') . '/links/links.inc';
            }
        }
    }

    /**
     * This function provides (part of) the general (shared) user
     * interface for links.
     *
     * @access public
     *
     * @param string $type
     * @param array  $link
     */
    function display($type, $link)
    {
        global $registry;

        $app = $this->_definitions[$type]['provider'];

        if ($registry->hasMethod($app . '/getLinkDescription')) {
            $description = $registry->call($app . '/getLinkDescription', array($link));
            if (is_a($description, 'PEAR_Error')) {
                Horde::logMessage($description, __FILE__, __LINE__, PEAR_LOG_ERR);
                printf(_("An error occurred following this link: %s"), $description->getMessage());
            } else {
                $url = $registry->link($app . '/followLink', $link['to_params']);
                if (!is_a($url, 'PEAR_Error')) {
                    $description = '<a href="' . Horde::url($url) . '">' . $description . '</a>';
                }
                echo $description;
            }
        } else {
            echo _("No description found");
        }

        if ($registry->hasMethod('deleteLink', 'horde') && !$this->_definitions[$type]['readonly']) {
            $url = $registry->linkByPackage('horde', 'deleteLink',
                                            array('link_data' => serialize($link),
                                                  'url' => Horde::selfURL(true, false, true)));
            echo '&nbsp;' . Horde::link(Horde::url($url), _("Delete this link")) . Horde::img('delete.gif', _("Delete"), '', $registry->getParam('graphics', 'horde')) . '</a>';
        }
    }

    /**
     * Add a link.
     *
     * @access public
     *
     * @param array $link_data      Contains the link's parameters
     */
    function addLink($link_data)
    {
        if (!isset($link_data['link_params']['from_application'])) {
            return PEAR::raiseError('No from_application specified.');
        }
        if (!isset($link_data['link_params']['to_application'])) {
            return PEAR::raiseError('No to_application specified.');
        }
        if (!isset($link_data['link_params']['link_type'])) {
            return PEAR::raiseError('No link_type specified.');
        }
        if (!isset($link_data['from_params'])) {
            return PEAR::raiseError('No from_params specified.');
        }
        if (!isset($link_data['to_params'])) {
            return PEAR::raiseError('No to_params specified.');
        }

        $this->_name = md5(uniqid(mt_rand(), true));
        $link = &new $this->_linkObject($this->_name);
        if (is_a($link, 'PEAR_Error')) {
            return PEAR::raiseError('Could not create link.');
        }

        if (!empty($link_data['link_params']['link_type'])
            && !empty($link_data['link_params']['from_application'])
            && !strstr($link_data['link_params']['link_type'], '/')) {
            $link_data['link_params']['link_type'] = $link_data['link_params']['from_application'] . '/' .
                                                     $link_data['link_params']['link_type'];
        }

        $link->addAttributes($link_data);

        return $this->_datatree->add($link);
    }

    /**
     * Delete a link.
     *
     * @access public
     *
     * @param array $link_data      Contains the link's parameters
     */
    function deleteLink($link_data)
    {
        if (!empty($link_data['link_params']['link_type'])
            && !empty($link_data['link_params']['from_application'])
            && !strstr($link_data['link_params']['link_type'], '/')) {
            $link_data['link_params']['link_type'] = $link_data['link_params']['from_application'] . '/' .
                                                     $link_data['link_params']['link_type'];
        }

        // First get all links meeting the supplied criteria.
        $links = $this->listLinks($link_data);

        // Now delete all these links from the DataTree driver.
        //
        // TODO: It would be better to do this in one batch (ie. pass
        // an array of names to be removed instead of looping over
        // them).
        foreach ($links as $link_id => $attributes) {
            $this->_datatree->remove($attributes['name']);
        }

        return false;
    }

    /**
     * Build DataTree criteria structure.
     *
	 * @access private
	 *
	 * @param array $link_criteria	Contains the link's parameters
	 */
    function _buildCriteria($link_criteria)
    {
        $term = 'AND';
        $criteria = array();
        foreach ($link_criteria as $name => $attributes) {
            if (is_array($attributes)) {
                foreach ($attributes as $key => $value) {
                    $c = array(array('field' => 'name', 'op' => '=', 'test' => $name),
                               array('field' => 'key', 'op' => '=', 'test' => $key));
                    if (!is_array($value)) {
                        $c[] = array('field' => 'value', 'op' => '=', 'test' => $value);
                    } else {
                        // Multiple values were specified. Return all
                        // links with any of the specified values
                        // (ie. use 'OR' for these values).
                        $valuelist = array();
                        foreach ($value as $val) {
                            $valuelist[] = array('field' => 'value', 'op' => '=', 'test' => $val);
                        }
                        $c[] = array('OR' => $valuelist);
                    }
                    $criteria[] = array($term => $c);

                    // Any further criteria should be JOINed.
                    $term = 'JOIN';
                }
            }
        }

        return array('AND' => $criteria);
    }

    /**
     * Attempts to return a reference to a concrete Horde_Links
     * instance. It will only create a new instance if no Horde_Links
     * instance with the same parameters currently exists.
     *
     * This method must be invoked as: $var = &Horde_Links::singleton()
     *
     * @param string $from_application  The 'provides' value for the
     *                                  application requesting the links
     *                                  or an application name.
     *
     * @return object Horde_Links  The concrete Horde_Links
     *                             reference or false on an error.
     *
     * @access public
     */
    function &singleton($from_application)
    {
        global $conf, $registry;

        static $instances = array();

        if ($registry->getParam('provides', $from_application) != '') {
            $from_application = $registry->getParam('provides', $from_application);
        }

        if (is_array($from_application)) {
            $from_application = $from_application[0];
        }

        if (empty($instances[$from_application])) {
            $instances[$from_application] = new Horde_Links($from_application);
        }

        return $instances[$from_application];
    }

}

/**
 * Extension of the DataTreeObject class for storing Link information
 * in the DataTree driver. If you want to store specialized Links
 * information, you should extend this class instead of extending
 * DataTreeObject directly.
 *
 * @package Horde_Links
 */
class DataTreeObject_Link extends DataTreeObject {

    /**
     * The Link object which this link came from - needed for
     * updating data in the backend to make changes stick, etc.
     *
     * @var object Horde_Links $_linkOb
     */
    var $_linkOb;

    function addAttributes($attributes = array())
    {
        $this->data[] = $attributes;
    }

    function _toAttributes()
    {
        $attributes = array();

        // Loop through all data elements, if any.
        foreach ($this->data as $index => $entry) {
            foreach ($entry as $name => $values) {
                foreach ($values as $key => $value) {
                    if (is_array($value)) {
                        $value = serialize($value);
                    }
                    $attributes[] = array('name' => (string)$name,
                                          'key' => (string)$key,
                                          'value' => $value);
                }
            }
        }

        return $attributes;
    }

}
