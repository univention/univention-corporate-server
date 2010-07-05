<?php
/**
 * $Horde: framework/View/lib/Horde/View/Helper/Block.php,v 1.1.2.1 2008-05-16 02:57:22 chuck Exp $
 *
 * @category Horde
 * @package Horde_View
 * @subpackage Helpers
 */

/**
 * View helper for displaying Horde_Block objects
 *
 * @category Horde
 * @package Horde_View
 * @subpackage Helpers
 */
class Horde_View_Helper_Block extends Horde_View_Helper {

    /**
     * Blocks that have already been fetched.
     *
     * @var array
     */
    protected $_blockCache = array();

    /**
     * Return the title of the specified block.
     *
     * @param string $app   The application the block is from.
     * @param string $block The name of the block to get the title for.
     * @param mixed $arg1   (optional) The first argument to the Block constructor.
     * @param mixed $arg2   (optional) The first argument to the Block constructor.
     * @param mixed $arg3   (optional) The first argument to the Block constructor.
     *
     * ...
     *
     * @return string The requested Block's title.
     *
     * @throws Horde_View_Exception, InvalidArgumentException
     */
    public function blockTitle()
    {
        $args = func_get_args();
        list($app, $block, $params) = $this->_args($args);

        return $this->_block($app, $block, $params)->getTitle();
    }

    /**
     * Return the content of the specified block.
     *
     * @param string $app   The application the block is from.
     * @param string $block The name of the block to get the content for.
     * @param mixed $arg1   (optional) The first argument to the Block constructor.
     * @param mixed $arg2   (optional) The first argument to the Block constructor.
     * @param mixed $arg3   (optional) The first argument to the Block constructor.
     *
     * ...
     *
     * @return string The requested Block's content.
     *
     * @throws Horde_View_Exception, InvalidArgumentException
     */
    public function blockContent()
    {
        $args = func_get_args();
        list($app, $block, $params) = $this->_args($args);

        return $this->_block($app, $block, $params)->getContent();
    }

    /**
     * Instantiate and cache Block objects
     *
     * @param string $app   The application the block is from.
     * @param string $block The name of the block to fetch.
     * @param array $params (option) Any arguments to the Block constructor.
     *
     * ...
     *
     * @return Horde_Block The requested Block object
     *
     * @throws Horde_View_Exception, InvalidArgumentException
     */
    protected function _block($app, $block, $params)
    {
        $hash = sha1(serialize(array($app, $block, $params)));
        if (!isset($this->_blockCache[$hash])) {
            $block = Horde_Block_Collection::getBlock($app, $block, $params);
            if (!$block instanceof Horde_Block) {
                if (is_callable(array($block, 'getMessage'))) {
                    throw new Horde_View_Exception($block->getMessage());
                } else {
                    throw new Horde_View_Exception('Unknown error instantiating Block object');
                }
            }

            $this->_blockCache[$hash] = $block;
        }

        return $this->_blockCache[$hash];
    }

    /**
     * Parse any argument style for the Block-fetching functions
     *
     * @param array $args
     */
    protected function _args($args)
    {
        $argc = count($args);

        if ($argc == 1) {
            if (is_array($args[0])) {
                $args = $args[0];
                $argc = count($args);
            }
        }

        if ($argc < 2) {
            throw new InvalidArgumentException('You must provide at least an application name and a block name.');
        }
        $app = array_shift($args);
        $block = array_shift($args);

        return array($app, $block, $args);
    }

}
