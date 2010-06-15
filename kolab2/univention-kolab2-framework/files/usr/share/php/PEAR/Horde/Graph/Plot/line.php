<?php
/**
 * Line graph implementation for the Horde_Graph package.
 *
 * $Horde: framework/Graph/Graph/Plot/line.php,v 1.4 2004/01/01 15:16:05 jan Exp $
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
class Horde_Graph_Plot_line {

    var $_graph;
    var $_color = 'blue';
    var $_width = 1;
    var $_dataset;

    function Horde_Graph_Plot_line(&$graph, $params)
    {
        $this->_graph = &$graph;

        foreach ($params as $param => $value) {
            $key = '_' . $param;
            $this->$key = $value;
        }
    }

    function draw()
    {
        $data = $this->_graph->_data['y'][$this->_dataset];

        $count = count($data);
        $verts = array();
        for ($i = 0; $i < $count; $i++) {
            $x = $i;
            $y = $data[$i];
            $this->_graph->translate($x, $y);
            $verts[] = array('x' => $x, 'y' => $y);
        }

        $this->_graph->img->polyline($verts, $this->_color, $this->_width);
    }

}
