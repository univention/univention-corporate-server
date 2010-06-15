<?php
/**
 * The Horde_Image_Decorator parent class defines a general API for
 * ways to "decorate" Horde_Image objects.
 *
 * $Horde: framework/Image/Image/Decorator.php,v 1.3 2004/05/04 21:35:10 chuck Exp $
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @package Horde_Image
 */
class Horde_Image_Decorator {

    /**
     * Decorator parameters.
     *
     * @var array $_params
     */
    var $_params = array();

    /**
     * Decorator constructor.
     *
     * @param array $params  (optional) Any parameters for the decoration.
     *                       Parameters are documented in each subclass.
     */
    function Horde_Image_Decorator($params = array())
    {
        foreach ($params as $key => $val) {
            $this->_params[$key] = $val;
        }
    }

}
