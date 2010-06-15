<?php
/**
 * $Horde: framework/Graph/tests/test05.php,v 1.6 2004/05/06 20:56:43 chuck Exp $
 *
 * @package Horde_Graph
 */

require_once dirname(__FILE__) . '/../Graph.php';

$graph = &new Horde_Graph(array('height' => 400, 'width' => 400));

$graph->set('title', 'One datapoint, two axis labels');
$graph->set('ylabel', 'Some Parameters');
$graph->set('xlabel', 'Day of the Week');
$graph->set('offsetGridX', .5);

$graph->addXData(array('Fri', 'Mon'));
$data1 = $graph->addYData(array(8.610));

$graph->addPlot('bar', array('dataset' => $data1, 'color' => 'red'));
$graph->addPlot('scatter', array('dataset' => $data1, 'color' => 'green'));
$graph->addPlot('line', array('dataset' => $data1, 'color' => 'blue'));

$graph->draw();
