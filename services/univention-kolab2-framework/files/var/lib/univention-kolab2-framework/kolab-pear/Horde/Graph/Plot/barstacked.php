<?php
/**
 * Stacked bar graph implementation for the Horde_Graph package.
 *
 * $Horde: framework/Graph/Graph/Plot/barstacked.php,v 1.1 2004/05/06 20:56:12 chuck Exp $
 *
 * Copyright 2002-2004 Chuck Hagenbuch <chuck@horde.org>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 3.0
 * @package Horde_Graph
 */
class Horde_Graph_Plot_barstacked {

    var $graph;

    var $_color = 'blue';
    var $_outline = 'black';
    var $_width = 10;
    var $_offset = 0;
    var $_dataset;

    function Horde_Graph_Plot_barstacked(&$graph, $params)
    {
        $this->graph = &$graph;

        foreach ($params as $param => $value) {
            $key = '_' . $param;
            $this->$key = $value;
        }
    }

    function draw()
    {
    }

}
