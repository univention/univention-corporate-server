<?php
/**
 * XML_SVG
 *
 * Wrapper class that provides some examples and a few convenience
 * methods.
 *
 * $Horde: framework/XML_SVG/SVG.php,v 1.16 2004/01/01 15:14:44 jan Exp $
 *
 * Copyright 2002-2004 Chuck Hagenbuch <chuck@horde.org>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @package XML_SVG
 */
class XML_SVG {

    function example()
    {
        // Create an instance of XML_SVG_Document. All other objects
        // will be added to this instance for printing. Set the height
        // and width of the viewport.
        $svg = &new XML_SVG_Document(array('width' => 400,
                                           'height' => 200));

        // Create an instance of XML_SVG_Group. Set the style,
        // transforms for child objects.
        $g = &new XML_SVG_Group(array('style' => 'stroke:black',
                                      'transform' => 'translate(200 100)'));

        // Add a parent to the g instance.
        $g->addParent($svg);

        // The same results can be accomplished by making g a child of the svg.
        // $svg->addChild($g);

        // Create and animate a circle.
        $circle = &new XML_SVG_Circle(array('cx' => 0,
                                           'cy' => 0,
                                           'r' => 100,
                                           'style' => 'stroke-width:3'));
        $circle->addChild(new XML_SVG_Animate(array('attributeName' => 'r',
                                                    'attributeType' => 'XML',
                                                    'from' => 0,
                                                    'to' => 75,
                                                    'dur' => '3s',
                                                    'fill' => 'freeze')));
        $circle->addChild(new XML_SVG_Animate(array('attributeName' => 'fill',
                                                    'attributeType' => 'CSS',
                                                    'from' => 'green',
                                                    'to' => 'red',
                                                    'dur' => '3s',
                                                    'fill' => 'freeze')));

        // Make the circle a child of g.
        $g->addChild($circle);

        // Create and animate some text.
        $text = &new XML_SVG_Text(array('text' => 'SVG chart!',
                                       'x' => 0,
                                       'y' => 0,
                                       'style' => 'font-size:20;text-anchor:middle;'));
        $text->addChild(new XML_SVG_Animate(array('attributeName' => 'font-size',
                                                  'attributeType' => 'auto',
                                                  'from' => 0,
                                                  'to' => 20,
                                                  'dur' => '3s',
                                                  'fill' => 'freeze')));

        // Make the text a child of g.
        $g->addChild($text);

        // Send a message to the svg instance to start printing.
        $svg->printElement();
    }

}

/**
 * XML_SVG_Element
 *
 * This is the base class for the different SVG Element
 * Objects. Extend this class to create a new SVG Element.
 *
 * @package XML_SVG
 */
class XML_SVG_Element {

    var $_elements = null;
    var $_style = null;
    var $_transform = null;
    var $_id = null;

    // The constructor.
    function XML_SVG_Element($params = array())
    {
        foreach ($params as $p => $v) {
            $param = '_' . $p;
            $this->$param = $v;
        }
    }

    // Most SVG elements can contain child elements. This method calls the
    // printElement method of any child element added to this object by use
    // of the addChild method.
    function printElement()
    {
        // Loop and call
        if (is_array($this->_elements)) {
            foreach ($this->_elements as $child) {
                $child->printElement();
            }
        }
    }

    // This method adds an object reference (or value, if $copy is
    // true) to the _elements array.
    function addChild(&$element, $copy = false)
    {
        if ($copy) {
            $this->_elements[] = $element;
        } else {
            $this->_elements[] = &$element;
        }
    }

    // This method sends a message to the passed element requesting to be
    // added as a child.
    function addParent(&$parent)
    {
        if (is_subclass_of($parent, 'XML_SVG_Element')) {
            $parent->addChild($this);
        }
    }

    function copy()
    {
        return $this;
    }

    // Print each of the passed parameters, if they are set.
    function printParams()
    {
        foreach (func_get_args() as $param) {
            $_param = '_' . $param;
            if (isset($this->$_param)) {
                switch ($param) {
                case 'filter':
                    echo ' filter="url(#' . $this->$_param . ')"';
                    break;

                default:
                    echo ' ' . str_replace('_', '-', $param) . '="' . $this->$_param . '"';
                    break;
                }
            }
        }
    }

    // Set any named attribute of an element to a value.
    function setParam($param, $value)
    {
        $attr = '_' . $param;
        $this->$attr = $value;
    }

    // Get any named attribute of an element.
    function getParam($param)
    {
        $attr = '_' . $param;
        if (isset($this->$attr)) {
            return $this->$attr;
        } else {
            return null;
        }
    }

    // Print out the object for debugging.
    function debug()
    {
        echo '<pre>'; var_dump($this); echo '</pre>';
    }

}

/** 
 * XML_SVG_Fragment
 *
 * @package XML_SVG
 */
class XML_SVG_Fragment extends XML_SVG_Element {

    var $_width;
    var $_height;
    var $_viewBox;
    var $_x;
    var $_y;

    function printElement()
    {
        echo '<svg';
        $this->printParams('id', 'width', 'height', 'x', 'y', 'viewBox', 'style');
        echo ' xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">' . "\n";
        parent::printElement();
        echo "</svg>\n";
    }

    function bufferObject()
    {
        ob_start();
        $this->printElement();
        $output = ob_get_contents();
        ob_end_clean();

        return $output;
    }
}

/**
 * XML_SVG_Document
 *
 * This extends the XML_SVG_Fragment class. It wraps the XML_SVG_Frament output
 * with a content header, xml definition and doctype.
 *
 * @package XML_SVG
 */
class XML_SVG_Document extends XML_SVG_Fragment {

    function printElement()
    {
        header('Content-Type: image/svg+xml');

        print('<?xml version="1.0" encoding="iso-8859-1"?>'."\n");
        print('<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.0//EN"
	        "http://www.w3.org/TR/2001/REC-SVG-20010904/DTD/svg10.dtd">' . "\n");

        parent::printElement();
    }

}

/** 
 * XML_SVG_Group
 *
 * @package XML_SVG
 */
class XML_SVG_Group extends XML_SVG_Element {

    function printElement()
    {
        echo '<g';
        $this->printParams('id', 'style', 'transform', 'filter');
        print(">\n");
        parent::printElement();
        print("</g>\n");
    }

}

/** 
 * XML_SVG_Textpath
 *
 * @package XML_SVG
 */
class XML_SVG_Textpath extends XML_SVG_Element {

    var $_text;
    var $_x;
    var $_y;
    var $_dx;
    var $_dy;
    var $_rotate;
    var $_textLength;
    var $_lengthAdjust;

    function printElement($element = 'textpath')
    {
        echo '<' . $element;
        $this->printParams('id', 'x', 'y', 'dx', 'dy', 'rotate',
                           'textLength', 'lengthAdjust', 'style', 'transform');
        echo '>' . htmlentities($this->_text);
        parent::printElement();
        echo "</$element>\n";
    }

    function setShape($x, $y, $text)
    {
        $this->_x = $x;
        $this->_y = $y;
        $this->_text = $text;
    }

}

/** 
 * XML_SVG_Text
 *
 * @package XML_SVG
 */
class XML_SVG_Text extends XML_SVG_Textpath {

    function printElement()
    {
        parent::printElement('text');
    }

    function setShape($x, $y, $text)
    {
        $this->_x = $x;
        $this->_y = $y;
        $this->_text = $text;
    }

}

/** 
 * XML_SVG_Tspan
 *
 * @package XML_SVG
 */
class XML_SVG_Tspan extends XML_SVG_Element {

    var $_text;
    var $_x;
    var $_y;
    var $_dx;
    var $_dy;
    var $_rotate;
    var $_textLength;
    var $_lengthAdjust;

    function printElement()
    {
        echo '<tspan';
        $this->printParams('id', 'x', 'y', 'dx', 'dy', 'rotate',
                           'textLength', 'lengthAdjust', 'style', 'transform');
        echo '>' . $this->_text;
        if (is_array($this->_elements)) {
            parent::printElement();
        }
        echo "</tspan>\n";
    }

    function setShape($x, $y, $text)
    {
        $this->_x = $x;
        $this->_y = $y;
        $this->_text  = $text;
    }

}

/** 
 * XML_SVG_Circle
 *
 * @package XML_SVG
 */
class XML_SVG_Circle extends XML_SVG_Element {

    var $_cx;
    var $_cy;
    var $_r;

    function printElement()
    {
        echo '<circle';

        $this->printParams('id', 'cx', 'cy', 'r', 'style', 'transform');
        if (is_array($this->_elements)) {
            // Print children, start and end tag.
            echo ">\n";
            parent::printElement();
            echo "</circle>\n";
        } else {
            // Print short tag.
            echo "/>\n";
        }
    }

    function setShape($cx, $cy, $r)
    {
        $this->_cx = $cx;
        $this->_cy = $cy;
        $this->_r  = $r;
    }

}

/** 
 * XML_SVG_Line
 *
 * @package XML_SVG
 */
class XML_SVG_Line extends XML_SVG_Element {

    var $_x1;
    var $_y1;
    var $_x2;
    var $_y2;

    function printElement()
    {
        echo '<line';
        $this->printParams('id', 'x1', 'y1', 'x2', 'y2', 'style');
        if (is_array($this->_elements)) {
            // Print children, start and end tag.
            print(">\n");
            parent::printElement();
            print("</line>\n");
        } else {
            // Print short tag.
            print("/>\n");
        }
    }

    function setShape($x1, $y1, $x2, $y2)
    {
        $this->_x1 = $x1;
        $this->_y1 = $y1;
        $this->_x2  = $x2;
        $this->_y2  = $y2;
    }

}

/** 
 * XML_SVG_Rect
 *
 * @package XML_SVG
 */
class XML_SVG_Rect extends XML_SVG_Element {

    var $_x;
    var $_y;
    var $_width;
    var $_height;
    var $_rx;
    var $_ry;

    function printElement()
    {
        echo '<rect';
        $this->printParams('id', 'x', 'y', 'width', 'height',
                           'rx', 'ry', 'style');
        if (is_array($this->_elements)) {
            // Print children, start and end tag.
            print(">\n");
            parent::printElement();
            print("</rect>\n");
        } else {
            // Print short tag.
            print("/>\n");
        }
    }

    function setShape($x, $y, $width, $height)
    {
        $this->_x = $x;
        $this->_y = $y;
        $this->_width  = $width;
        $this->_height  = $height;
    }

}

/** 
 * XML_SVG_Ellipse
 *
 * @package XML_SVG
 */
class XML_SVG_Ellipse extends XML_SVG_Element {

    var $_cx;
    var $_cy;
    var $_rx;
    var $_ry;

    function printElement()
    {
        echo '<ellipse';
        $this->printParams('id', 'cx', 'cy', 'rx', 'ry', 'style', 'transform');
        if (is_array($this->_elements)) {
            // Print children, start and end tag.
            print(">\n");
            parent::printElement();
            print("</ellipse>\n");
        } else {
            // Print short tag.
            print(" />\n");
        }
    }

    function setShape($cx, $cy, $rx, $ry)
    {
        $this->_cx = $cx;
        $this->_cy = $cy;
        $this->_rx  = $rx;
        $this->_ry  = $ry;
    }

}

/** 
 * XML_SVG_Polyline
 *
 * @package XML_SVG
 */
class XML_SVG_Polyline extends XML_SVG_Element {

    var $_points;

    function printElement()
    {
        echo '<polyline';
        $this->printParams('id', 'points', 'style', 'transform');

        if (is_array($this->_elements)) {
            // Print children, start and end tag.
            print(">\n");
            parent::printElement();
            print("</polyline>\n");
        } else {
            // Print short tag.
            print("/>\n");
        }
    }

    function setShape($points)
    {
        $this->_points = $points;
    }

}

/** 
 * XML_SVG_Polygon
 *
 * @package XML_SVG
 */
class XML_SVG_Polygon extends XML_SVG_Element {

    var $_points;

    function printElement()
    {
        echo '<polygon';
        $this->printParams('id', 'points', 'style', 'transform');
        if (is_array($this->_elements)) {
            // Print children, start and end tag.
            print(">\n");
            parent::printElement();
            print("</polygon>\n");
        } else {
            // Print short tag.
            print("/>\n");
        }
    }

    function setShape($points)
    {
        $this->_points = $points;
    }

}

/** 
 * XML_SVG_Path
 *
 * @package XML_SVG
 */
class XML_SVG_Path extends XML_SVG_Element {

    var $_d;

    function printElement()
    {
        echo '<path';
        $this->printParams('id', 'd', 'style', 'transform');
        if (is_array($this->_elements)) {
            // Print children, start and end tag.
            print(">\n");
            parent::printElement();
            print("</path>\n");
        } else {
            // Print short tag.
            print("/>\n");
        }
    }

    function setShape($d)
    {
        $this->_d = $d;
    }

}

/** 
 * XML_SVG_Image
 *
 * @package XML_SVG
 */
class XML_SVG_Image extends XML_SVG_Element {

    var $_x;
    var $_y;
    var $_width;
    var $_height;
    var $_href;

    function printElement()
    {
        echo '<image';
        $this->printParams('id', 'x', 'y', 'width', 'height', 'style');
        if (!empty($this->_href)) {
            echo ' xlink:href="' . $this->_href . '"';
        }
        if (is_array($this->_elements)) {
            // Print children, start and end tag.
            echo ">\n";
            parent::printElement();
            echo "</image>\n";
        } else {
            // Print short tag.
            echo " />\n";
        }
    }

    function setShape($x, $y, $width, $height)
    {
        $this->_x = $x;
        $this->_y = $y;
        $this->_width  = $width;
        $this->_height  = $height;
    }

}

/** 
 * XML_SVG_Animate
 *
 * @package XML_SVG
 */
class XML_SVG_Animate extends XML_SVG_Element {

    var $_attributeName;
    var $_attributeType;
    var $_from;
    var $_to;
    var $_begin;
    var $_dur;
    var $_fill;

    function printElement()
    {
        echo '<animate';
        $this->printParams('id', 'attributeName', 'attributeType', 'from', 'to',
                           'begin', 'dur', 'fill');
        if (is_array($this->_elements)) {
            // Print children, start and end tag.
            echo ">\n";
            parent::printElement();
            echo "</animate>\n";
        } else {
            echo " />\n";
        }
    }

    function setShape($attributeName, $attributeType = '', $from = '',
                      $to = '', $begin = '', $dur = '', $fill = '')
    {
        $this->_attributeName = $attributeName;
        $this->_attributeType = $attributeType;
        $this->_from  = $from;
        $this->_to = $to;
        $this->_begin = $begin;
        $this->_dur = $dur;
        $this->_fill = $fill;
    }

}

/** 
 * XML_SVG_Filter
 *
 * @package XML_SVG
 */
class XML_SVG_Filter extends XML_SVG_Element {

    function printElement()
    {
        echo '<filter';
        $this->printParams('id');
        if (is_array($this->_elements)) {
            // Print children, start and end tag.
            echo ">\n";
            parent::printElement();
            echo "</filter>\n";
        } else {
            echo " />\n";
        }
    }

    function addPrimitive($primitive, $params)
    {
        $this->addChild(new XML_SVG_FilterPrimitive($primitive, $params));
    }

}

/** 
 * XML_SVG_FilterPrimitive
 *
 * @package XML_SVG
 */
class XML_SVG_FilterPrimitive extends XML_SVG_Element {

    var $_primitives = array('Blend',
                             'ColorMatrix',
                             'ComponentTransfer',
                             'Composite',
                             'ConvolveMatrix',
                             'DiffuseLighting',
                             'DisplacementMap',
                             'Flood',
                             'GaussianBlur',
                             'Image',
                             'Merge',
                             'Morphology',
                             'Offset',
                             'SpecularLighting',
                             'Tile',
                             'Turbulence');

    var $_primitive;

    var $_in;
    var $_in2;
    var $_result;
    var $_x;
    var $_y;
    var $_dx;
    var $_dy;
    var $_width;
    var $_height;
    var $_mode;
    var $_type;
    var $_values;
    var $_operator;
    var $_k1;
    var $_k2;
    var $_k3;
    var $_k4;
    var $_surfaceScale;
    var $_diffuseConstant;
    var $_kernelUnitLength;
    var $_floor_color;
    var $_flood_opacity;

    function XML_SVG_FilterPrimitive($primitive, $params = array())
    {
        parent::XML_SVG_Element($params);
        $this->_primitive = $primitive;
    }

    function printElement()
    {
        $name = 'fe' . $this->_primitive;
        echo '<' . $name;
        $this->printParams('id', 'x', 'y', 'dx', 'dy', 'width', 'height', 'in', 'in2',
                           'result', 'mode', 'type', 'values', 'operator',
                           'k1', 'k2', 'k3', 'k4', 'surfaceScale', 'stdDeviation',
                           'diffuseConstant', 'kernelUnitLength',
                           'flood_color', 'flood_opacity');
        if (is_array($this->_elements)) {
            // Print children, start and end tag.
            echo ">\n";
            parent::printElement();
            echo '</' . $name . '>';
        } else {
            echo '/>';
        }
    }

    /**
     * For feMerge elements.
     */
    function addMergeNode($in)
    {
        $this->addChild(new XML_SVG_FilterMergeNode(array('in' => $in)));
    }

}

/** 
 * XML_SVG_FilterMergeNode
 *
 * @package XML_SVG
 */
class XML_SVG_FilterMergeNode extends XML_SVG_Element {

    var $_in;

    function printElement()
    {
        echo '<feMergeNode';
        $this->printParams('in');
        echo '/>';
    }

}

/** 
 * XML_SVG_Use
 *
 * @package XML_SVG
 */
class XML_SVG_Use extends XML_SVG_Element {

    var $_symbol;

    function XML_SVG_Use($symbol, $params = array())
    {
        parent::XML_SVG_Element($params);
        $this->_symbol = $symbol;
    }

    function printElement()
    {
        echo '<use xlink:href="#' . $this->_symbol . '"/>';
    }

}

/** 
 * XML_SVG_Defs
 *
 * @package XML_SVG
 */
class XML_SVG_Defs extends XML_SVG_Element {

    function printElement()
    {
        echo '<defs';
        $this->printParams('id', 'style', 'transform');
        echo ">\n";
        parent::printElement();
        echo "</defs>\n";
    }

}

/** 
 * XML_SVG_Marker
 *
 * @package XML_SVG
 */
class XML_SVG_Marker extends XML_SVG_Element {

    var $_refX;
    var $_refY;
    var $_markerUnits;
    var $_markerWidth;
    var $_markerHeight;
    var $_orient;

    function printElement()
    {
        echo '<marker';
        $this->printParams('id', 'refX', 'refY', 'markerUnits',
                           'markerWidth', 'markerHeight', 'orient');
        if (is_array($this->_elements)) { // Print children, start and end tag.
            print(">\n");
            parent::printElement();
            print("</marker>\n");
        } else {
            print("/>\n");
        }
    }

    function setShape($refX = '', $refY = '', $markerUnits = '',
                      $markerWidth = '', $markerHeight = '', $orient = '')
    {
        $this->_refX = $refX;
        $this->_refY  = $refY;
        $this->_markerUnits = $markerUnits;
        $this->_markerWidth = $markerWidth;
        $this->_markerHeight = $markerHeight;
        $this->_orient = $orient;
    }

}

/** 
 * XML_SVG_Title 
 *
 * @package XML_SVG
*/
class XML_SVG_Title extends XML_SVG_Element {

    var $_title;

    function printElement()
    {
        echo '<title';
        $this->printParams('id', 'style');
        print(">\n");
        print($this->_title);
        parent::printElement();
        print("</title>\n");
    }

}

/** 
 * XML_SVG_Desc
 *
 * @package XML_SVG
 */
class XML_SVG_Desc extends XML_SVG_Element {

    var $_desc;

    function printElement()
    {
        echo '<desc';
        $this->printParams('id', 'style');
        echo '>' . $this->_desc;
        parent::printElement();
        echo "</desc>\n";
    }

}

/** 
 * XML_SVG_Tref
 *
 * @package XML_SVG
 */
class XML_SVG_Tref extends XML_SVG_Element {

    var $_text;
    var $_x;
    var $_y;
    var $_dx;
    var $_dy;
    var $_rotate;
    var $_textLength;
    var $_lengthAdjust;

    function printElement()
    {
        echo '<tref';
        $this->printParams('id', 'x', 'y', 'dx', 'dy', 'rotate',
                           'textLength', 'lengthAdjust', 'style');
        echo '>' . $this->_text;
        parent::printElement();
        echo "</tref>\n";
    }

}
