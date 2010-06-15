<?php
/**
 * $Horde: framework/Graph/tests/test_bargrouped.php,v 1.1 2004/05/06 21:14:56 chuck Exp $
 *
 * @package Horde_Graph
 */

require_once dirname(__FILE__) . '/../Graph.php';

$graph = &new Horde_Graph(array('height' => 400, 'width' => 400));

$graph->set('title', 'Grouped Bars');
$graph->set('ylabel', 'Value');
$graph->set('xlabel', 'Day of the Week');
$graph->set('offsetGridX', .5);

$graph->addXData(array('Fri', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri'));
$data1 = $graph->addYData(array(8.610, 7.940, 3.670, 3.670, 6.940, 8.650));
$data2 = $graph->addYData(array(1.456, 3.001, 5.145, 2.050, 1.998, 1.678));
$data3 = $graph->addYData(array(4.896, 4.500, 4.190, 3.050, 2.888, 3.678));

$graph->addPlot('bargrouped', array('datasets' => array($data1, $data2, $data3), 'colors' => array('red', 'green', 'blue')));

$graph->draw();
