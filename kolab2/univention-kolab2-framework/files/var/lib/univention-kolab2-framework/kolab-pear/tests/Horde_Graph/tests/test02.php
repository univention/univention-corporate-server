<?php
/**
 * $Horde: framework/Graph/tests/test02.php,v 1.8 2004/05/06 20:56:43 chuck Exp $
 *
 * @package Horde_Graph
 */

require_once dirname(__FILE__) . '/../Graph.php';

$graph = &new Horde_Graph(array('height' => 400, 'width' => 400));

$graph->set('title', '3 bars');
$graph->set('ylabel', 'Some Parameters');
$graph->set('xlabel', 'Day of the Week');
$graph->set('offsetGridX', .5);

$graph->addXData(array('Fri', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri'));
$data1 = $graph->addYData(array(8.610, 7.940, 3.670, 3.670, 6.940, 8.650));
$data2 = $graph->addYData(array(1.456, 3.001, 5.145, 2.050, 1.998, 1.678));
$data3 = $graph->addYData(array(4.896, 4.500, 4.190, 3.050, 2.888, 3.678));

$graph->addPlot('bar', array('dataset' => $data3, 'offset' => .5, 'color' => 'blue'));
$graph->addPlot('bar', array('dataset' => $data2, 'offset' => 0, 'color' => 'green'));
$graph->addPlot('bar', array('dataset' => $data1, 'offset' => -.5, 'color' => 'red'));

$graph->draw();
