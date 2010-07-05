<?php
/**
 * Horde_UI_TagCloud:: for creating and displaying tag clouds.
 *
 * Based on a striped down version of Pear's HTML_TagCloud
 *
 * $Horde: framework/UI/UI/TagCloud.php,v 1.9.2.2 2008-01-20 21:20:43 mrubinsk Exp $
 *
 * @since   Horde 3.2
 * @package Horde
 */

class Horde_UI_TagCloud {

    /**
     * @var    array
     */
    var $_elements = array();

    /**
     * @var    int
     * @access public
     */
    var $basefontsize = 24;

    /**
     * @var    int
     */
    var $fontsizerange = 12;

    /**
     * @var    int
     */
    var $_max = 0;

    /**
     * @var    int
     */
    var $_min = 0;

    /**
     * @var    int
     */
    var $_max_epoc;

    /**
     * @var    int
     */
    var $_min_epoc;

    /**
     * @var    string
     */
    var $css_class = 'tagcloud';

    /**
     * @var    string
     * mm,cm,in,pt,pc,px,em
     */
    var $size_suffix = 'px';

    /**
     * @var    int
     */
    var $factor;

    /**
     * @var    array
     */
    var $epoc_level = array(
            'earliest',
            'earlier',
            'later',
            'latest'
    );

    /**
     * @var array
     */
    var $_map = array();

    /**
     * Class constructor
     *
     * @param   int $basefontsize    base font size of output tag (option)
     * @param   int $fontsizerange   font size range
     * @access  public
     */
    function Horde_UI_TagCloud($basefontsize = 24, $fontsizerange = 12)
    {
        $this->basefontsize = $basefontsize;
        $this->minfontsize = ($this->basefontsize - $this->fontsizerange > 0) ? $this->basefontsize - $this->fontsizerange : 0;
        $this->maxfontsize = $this->basefontsize + $this->fontsizerange;
    }

    /**
     * add a Tag Element to build Tag Cloud
     *
     * @return  void
     * @param   string  $tag
     * @param   string  $url
     * @param   int     $count
     * @param   int     $timestamp unixtimestamp
     * @param   string  $onclick   javascript onclick event handler
     *
     * @access  public
     */
    function addElement($name, $url ='', $count = 0, $timestamp = null,
                        $onclick = null)
    {

        if (isset($this->_map[$name])) {
            $i = $this->_map[$name];
            // Increase the count
            $this->_elements[$i]['count'] += $count;

            // Keep the latest timestamp
            if (!empty($timestamp) &&
                $timestamp > $this->_elements[$i]['timestamp']) {
                $this->_elements[$i]['timestamp'] = $timestamp;
            }
            // For onclick and url we will simply overwrite the existing values
            // instead of checking if they are empty, then overwriting.
            $this->_elements[$i]['onclick'] = $onclick;
            $this->elements[$i]['url'] = $url;
        } else {
            $i = count($this->_elements);
            $this->_elements[$i]['name'] = $name;
            $this->_elements[$i]['url'] = $url;
            $this->_elements[$i]['count'] = $count;
            $this->_elements[$i]['timestamp'] = $timestamp == null ? time() : $timestamp;
            $this->_elements[$i]['onclick'] = $onclick;
            $this->_map[$name] = $i;
        }
    }

    /**
     * add a Tag Element to build Tag Cloud
     *
     * @return  void
     * @param   array   $tags Associative array to $this->_elements
     * @access  public
     */
    function addElements($tags)
    {
        $this->_elements = array_merge($this->_elements, $tags);
    }

    /**
     * clear Tag Elements
     *
     * @access  public
     */
    function clearElements()
    {
        $this->_elements = array();
    }

    /**
     * build HTML part
     *
     * @return  string HTML
     * @param   array  $param 'limit' => int limit of generation tag num.
     * @access  public
     */
    function buildHTML($param = array())
    {
        return $this->_wrapDiv($this->_buidHTMLTags($param));
    }

    /**
     * calc Tag level and create whole HTML of each Tags
     *
     * @return  string HTML
     * @param   array $param limit of Tag Number
     * @access  private
     */
    function _buidHTMLTags($param)
    {
        $this->total = count($this->_elements);
        // no tags elements
        if ($this->total == 0) {
            return '';
        } elseif ($this->total == 1) {
            $tag = $this->_elements[0];
            return $this->_createHTMLTag($tag, 'latest', $this->basefontsize);
        }

        $limit = array_key_exists('limit', $param) ? $param['limit'] : 0;
        $this->_sortTags($limit);
        $this->_calcMumCount();
        $this->_calcMumEpoc();

        $range = $this->maxfontsize - $this->minfontsize;
        $this->factor = $this->_max == $this->_min ? 1
                                                 : $range / (sqrt($this->_max) - sqrt($this->_min));
        $this->epoc_factor = $this->_max_epoc == $this->_min_epoc ? 1
                                                                : count($this->epoc_level) / (sqrt($this->_max_epoc) - sqrt($this->_min_epoc));
        $rtn = array();
        foreach ($this->_elements as $tag){
            $count_lv = $this->_getCountLevel($tag['count']);
            if(! isset($tag['timestamp']) || empty($tag['timestamp'])){
                $epoc_lv = count($this->epoc_level) - 1;
            }else{
                $epoc_lv  = $this->_getEpocLevel($tag['timestamp']);
            }
            $color_type = $this->epoc_level[$epoc_lv];
            $font_size  = $this->minfontsize + $count_lv;
            $rtn[] = $this->_createHTMLTag($tag, $color_type, $font_size);
        }
        return implode("", $rtn);
    }

    /**
     * create a Element of HTML part
     *
     * @return  string a Element of Tag HTML
     * @param   array  $tag
     * @param   string $type css class of time line param
     * @param   int    $fontsize
     * @access  private
     */
    function _createHTMLTag($tag, $type, $fontsize)
    {
        return sprintf("<a style=\"font-size: %d%s\" class=\"%s\" href=\"%s\" %s >%s</a>\n",
                       $fontsize,
                       $this->size_suffix,
                       $type,
                       $tag['url'],
                       (empty($tag['onclick']) ? '' : 'onClick="' . $tag['onclick'] . '"'),
                       htmlspecialchars($tag['name']));
    }

    /**
     * sort tags by name
     *
     * @return  array
     * @param   int  $limit limit element number of create TagCloud
     * @access  private
     */
    function _sortTags($limit = 0){
        usort($this->_elements, array(get_class($this), "_cmpElementsName"));
        if ($limit != 0){
            $this->_elements = array_splice($this->_elements, 0, $limit);
        }
    }

    /**
     * using for usort()
     *
     * @return  int
     * @access  private
     */
    function _cmpElementsName($a, $b)
    {
        if ($a['name'] == $b['name']) {
            return 0;
        }
        return ($a['name'] < $b['name']) ? -1 : 1;
    }

    /**
     * calc max and min tag count of use
     *
     * @access  private
     */
    function _calcMumCount()
    {
        foreach($this->_elements as $item){
            $array[] = $item['count'];
        }
        $this->_min = min($array);
        $this->_max = max($array);
    }

    /**
     * calc max and min timestamp
     *
     * @access  private
     */
    function _calcMumEpoc()
    {
        foreach($this->_elements as $item){
            $array[] = $item['timestamp'];
        }
        $this->_min_epoc = min($array);
        $this->_max_epoc = max($array);
    }

    /**
     * calc Tag Level of size
     *
     * @return  int level
     * @param   int $count
     * @access  private
     */
    function _getCountLevel($count = 0)
    {
        return (int)(sqrt($count) - sqrt($this->_min) ) * $this->factor;
    }

    /**
     * calc timeline level of Tag
     *
     * @return  int level of timeline
     * @param   int     $timestamp
     * @access  private
     */
    function _getEpocLevel($timestamp = 0)
    {
        return (int)(sqrt($timestamp) - sqrt($this->_min_epoc)) * $this->epoc_factor;
    }

    /**
     * wrap div tag
     *
     * @return  string
     * @param   string $html
     * @access  private
     */
    function _wrapDiv($html)
    {
        return $html == "" ? "" : sprintf("<div class=\"%s\">\n%s</div>\n", $this->css_class, $html);
    }

}
