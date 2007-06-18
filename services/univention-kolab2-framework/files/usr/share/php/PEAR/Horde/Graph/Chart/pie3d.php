<?php
/**
 * 3D Pie graph implementation for the Horde_Graph package.
 *
 * $Horde: framework/Graph/Graph/Chart/pie3d.php,v 1.1 2004/05/06 20:56:12 chuck Exp $
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
class Horde_Graph_Chart_pie3d {

    var $graph;

    var $_dataset;
    var $_padding = 20;
    var $_outline = true;
    var $_colors = array('tan', 'palegoldenrod', 'olivedrab', 'blue', 'red', 'green', 'yellow',
                         'orange', 'gray', 'purple');
    /**
      "255,153,0",
      "0,204,153",
      "204,255,102",
      "255,102,102",
      "102,204,255",
      "204,153,255",
      "255,0,0",
      "51,0,255",
      "255,51,153",
      "204,0,255",
      "255,255,51",
      "51,255,51",
      "255,102,0");
    */

    function Horde_Graph_Chart_pie3d(&$graph, $params)
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
