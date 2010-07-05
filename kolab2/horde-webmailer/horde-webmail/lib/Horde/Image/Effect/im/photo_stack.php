<?php
/**
 * Effect for composing multiple images into a single image.
 *
 * The technique for the Polaroid-like stack using the Imagick extension is
*  credited to Mikko Koppanen and is documented at http://valokuva.org
 *
 * $Horde: framework/Image/Image/Effect/im/photo_stack.php,v 1.33.2.4 2009-03-23 18:15:48 mrubinsk Exp $
 *
 * @author  Michael J. Rubinsky <mrubinsk@horde.org>
 * @since   Horde 3.2
 * @package Horde_Image
 */
class Horde_Image_Effect_im_photo_stack extends Horde_Image_Effect {

    /**
     * Valid parameters for the stack effect
     *
     * images           -    An array of Horde_Image objects to stack. Images
     *                       are stacked in a FIFO manner, so that the top-most
     *                       image is the last one in this array.
     *
     * type             -    Determines the style for the composition.
     *                       'plain' or 'polaroid' are supported.
     *
     * resize_height    -    The height that each individual thumbnail
     *                       should be resized to before composing on the image.
     *
     * padding          -    How much padding should we ensure is left around
     *                       the active image area?
     *
     * background       -    The background canvas color - this is used as the
     *                       color to set any padding to.
     *
     * bordercolor      -    If using type 'plain' this sets the color of the
     *                       border that each individual thumbnail gets.
     *
     * borderwidth      -    If usin type 'plain' this set the width of the
     *                       border on each individual thumbnail.
     *
     * offset           -    If using type 'plain' this determines the amount of
     *                       x and y offset to give each successive image when
     *                       it is placed on the top of the stack.
     *
     * @var array
     */
    var $_params = array('type' => 'plain',
                         'resize_height' => '150',
                         'padding' => 0,
                         'background' => 'none',
                         'bordercolor' => '#333',
                         'borderwidth' => 1,
                         'borderrounding' => 10,
                         'offset' => 5
                         );

    /**
     * Create the photo_stack
     *
     */
    function apply()
    {
        $i = 1;
        $cnt = count($this->_params['images']);
        if ($cnt <=0) {
            return PEAR::raiseError('No images provided');
        }
        if (!is_null($this->_image->_imagick) &&
            $this->_image->_imagick->methodExists('polaroidImage') &&
            $this->_image->_imagick->methodExists('trimImage')) {

            $imgs = array();
            $length = 0;

            switch ($this->_params['type']) {
            case 'plain':
            case 'rounded':
                $haveBottom = false;
                // First, we need to resize the top image to get the dimensions
                // for the rest of the stack.
                $topimg = new Horde_Image_ImagickProxy();
                $topimg->clear();
                $topimg->readImageBlob($this->_params['images'][$cnt - 1]->raw());
                $topimg->thumbnailImage(
                    $this->_params['resize_height'],
                    $this->_params['resize_height'],
                    true);
                if ($this->_params['type'] == 'rounded') {
                    $topimg = $this->_roundBorder($topimg);
                }

                $size = $topimg->getImageGeometry();
                foreach ($this->_params['images'] as $image) {
                    $imgk= new Horde_Image_ImagickProxy();
                    $imgk->clear();
                    $imgk->readImageBlob($image->raw());
                    if ($i++ <= $cnt) {
                        $imgk->thumbnailImage($size['width'], $size['height'],
                                              false);
                    } else {
                        $imgk->destroy();
                        $imgk = $topimg->cloneIM();
                    }

                    if ($this->_params['type'] == 'rounded') {
                        $imgk = $this->_roundBorder($imgk);
                    } else {
                        $imgk->borderImage($this->_params['bordercolor'], 1, 1);
                    }
                    // Only shadow the bottom image for 'plain' stacks
                    if (!$haveBottom) {
                        $shad = $imgk->cloneIM();
                        $shad->setImageBackgroundColor('black');
                        $shad->shadowImage(80, 4, 0, 0);
                        $shad->compositeImage($imgk,
                                              constant('Imagick::COMPOSITE_OVER'),
                                              0, 0);
                        $imgk->clear();
                        $imgk->addImage($shad);
                        $shad->destroy();
                        $haveBottom = true;
                    }
                    // Get the geometry of the image and remember the largest.
                    $geo = $imgk->getImageGeometry();
                    $length = max(
                        $length,
                        sqrt(pow($geo['height'], 2) + pow($geo['width'], 2)));

                    $imgs[] = $imgk;
                }
                break;
            case 'polaroid':
                foreach ($this->_params['images'] as $image) {
                    $imgk= new Horde_Image_ImagickProxy();
                    $imgk->clear();
                    $imgk->readImageBlob($image->raw());
                    $imgk->thumbnailImage($this->_params['resize_height'],
                                          $this->_params['resize_height'],
                                          true);
                    $imgk->setImageBackgroundColor('black');
                    if ($i++ == $cnt) {
                        $angle = 0;
                    } else {
                        $angle = mt_rand(1, 45);
                        if (mt_rand(1, 2) % 2 === 0) {
                            $angle = $angle * -1;
                        }
                    }
                    $result = $imgk->polaroidImage($angle);
                    if (is_a($result, 'PEAR_Error')) {
                        return $result;
                    }
                     // Get the geometry of the image and remember the largest.
                    $geo = $imgk->getImageGeometry();
                    $length = max(
                        $length,
                        sqrt(pow($geo['height'], 2) + pow($geo['width'], 2)));

                    $imgs[] = $imgk;
                }
                break;
            }

            // Make sure the background canvas is large enough to hold it all.
            $this->_image->_imagick->thumbnailImage($length * 1.5 + 20,
                                                    $length * 1.5 + 20);

            // x and y offsets.
            $xo = $yo = (count($imgs) + 1) * $this->_params['offset'];
            foreach ($imgs as $image) {
                if ($this->_params['type'] == 'polaroid') {
                    $xo = mt_rand(1, $this->_params['resize_height'] / 2);
                    $yo = mt_rand(1, $this->_params['resize_height'] / 2);
                } elseif ($this->_params['type'] == 'plain' ||
                          $this->_params['type'] == 'rounded') {
                    $xo -= $this->_params['offset'];
                    $yo -= $this->_params['offset'];
                }

                $this->_image->_imagick->compositeImage(
                    $image, constant('Imagick::COMPOSITE_OVER'), $xo, $yo);
                $image->removeImage();
                $image->destroy();
            }
            // If we have a background other than 'none' we need to
            // compose two images together to make sure we *have* a background.
            if ($this->_params['background'] != 'none') {
                $size = $this->_image->getDimensions();
                $new = new Horde_Image_ImagickProxy($length * 1.5 + 20,
                                                    $length * 1.5 + 20,
                                                    $this->_params['background'],
                                                    $this->_image->_type);



                $new->compositeImage($this->_image->_imagick,
                                     constant('Imagick::COMPOSITE_OVER'), 0, 0);
                $this->_image->_imagick->clear();
                $this->_image->_imagick->addImage($new);
                $new->destroy();
            }
            // Trim the canvas before resizing to keep the thumbnails as large
            // as possible.
            $this->_image->_imagick->trimImage(0);
            if ($this->_params['padding']) {
                $this->_image->_imagick->borderImage($this->_params['background'],
                                                     $this->_params['padding'],
                                                     $this->_params['padding']);
            }

        } else {
            // No Imagick installed - use im, but make sure we don't mix imagick
            // and convert.
            $this->_image->_imagick = null;
            $this->_image->raw();

            switch ($this->_params['type']) {
            case 'plain':
            case 'rounded':
                // Get top image dimensions, then force each bottom image to the
                // same dimensions.
                $this->_params['images'][$cnt - 1]->resize($this->_params['resize_height'],
                                                           $this->_params['resize_height'],
                                                           true);
                $size = $this->_params['images'][$cnt - 1]->getDimensions();
                //$this->_image->resize(2 * $this->_params['resize_height'], 2 * $this->_params['resize_height']);
                for ($i = 0; $i < $cnt; $i++) {
                    $this->_params['images'][$i]->resize($size['height'], $size['width'], false);
                }
                $xo = $yo = (count($this->_params['images']) + 1) * $this->_params['offset'];
                $ops = '';
                $haveBottom = false;
                foreach ($this->_params['images'] as $image) {
                    $xo -= $this->_params['offset'];
                    $yo -= $this->_params['offset'];

                    if ($this->_params['type'] == 'rounded') {
                        $temp = $this->_roundBorder($image);
                    } else {
                        $temp = $image->toFile();
                    }
                    $this->_image->_toClean[] = $temp;
                    $ops .= ' \( ' . $temp . ' -background none -thumbnail ' . $size['width'] . 'x' . $size['height'] . '! -repage +' . $xo . '+' . $yo . ($this->_params['type'] == 'plain' ? ' -bordercolor "#333" -border 1 ' : ' ' ) . ((!$haveBottom) ? '\( +clone -shadow 80x4+0+0 \) +swap -mosaic' : '') . ' \) ';
                    $haveBottom = true;
                }

                // The first -background none option below is only honored in
                // convert versions before 6.4 it seems. Without it specified as
                // none here, all stacks come out with a white background.
                $this->_image->_postSrcOperations[] = $ops . ' -background ' . $this->_params['background'] . ' -mosaic -bordercolor ' . $this->_params['background'] . ' -border ' . $this->_params['padding'];

                break;

            case 'polaroid':
                // Check for im version > 6.3.2
                $ver = $this->_image->_getIMVersion();
                if (is_array($ver) && version_compare($ver[0], '6.3.2') >= 0) {
                    $ops = '';
                    foreach ($this->_params['images'] as $image) {
                        $temp = $image->toFile();
                        // Remember the temp files so we can nuke them later.
                        $this->_image->_toClean[] = $temp;

                        // Don't rotate the top image.
                        if ($i++ == $cnt) {
                            $angle = 0;
                        } else {
                            $angle = mt_rand(1, 45);
                            if (mt_rand(1, 2) % 2 === 0) {
                                $angle = $angle * -1;
                            }
                        }
                        $ops .= ' \( ' . $temp . ' -geometry +' . mt_rand(1, $this->_params['resize_height']) . '+' . mt_rand(1, $this->_params['resize_height']) . ' -thumbnail \'' . $this->_params['resize_height'] . 'x' . $this->_params['resize_height'] . '>\' -bordercolor Snow -border 1 -polaroid ' . $angle . ' \) ';
                    }
                    $this->_image->_postSrcOperations[] = '-background none' . $ops . '-mosaic -bordercolor ' . $this->_params['background'] . ' -border ' . $this->_params['padding'];
                } else {
                    // An attempt at a -polaroid command free version of this
                    // effect based on various examples and ideas at
                    // http://imagemagick.org
                    $ops = '';
                    foreach ($this->_params['images'] as $image) {
                        $temp = $image->toFile();
                        $this->_image->_toClean[] = $temp;
                        if ($i++ == $cnt) {
                            $angle = 0;
                        } else {
                            $angle = mt_rand(1, 45);
                            if (mt_rand(1, 2) % 2 === 0) {
                                $angle = $angle * -1;
                            }
                        }
                        $ops .= '\( ' . $temp . ' -thumbnail \'' . $this->_params['resize_height'] . 'x' . $this->_params['resize_height']. '>\' -bordercolor "#eee" -border 4 -bordercolor grey90 -border 1 -bordercolor none -background none -rotate ' . $angle . ' -background none \( +clone -shadow 60x4+4+4 \) +swap -background none -flatten \) ';
                    }
                    $this->_image->_postSrcOperations[] = '-background none ' . $ops . '-mosaic -trim +repage -bordercolor ' . $this->_params['background'] . ' -border ' . $this->_params['padding'];
                }
                break;
            }
        }

        return true;
    }

    function _roundBorder($image)
    {
        if (!is_null($this->_image->_imagick)) {
            $size = $image->getImageGeometry();
            $params = array('temp' => $this->_image->_tmpdir);
            $new = Horde_Image::factory('im', $params);
            $new->loadString('somestring', $image->getImageBlob());
            $image->destroy();
            $new->addEffect('round_corners', array('border' => 2, 'bordercolor' => '#111'));
            $new->applyEffects();
            $return  = new Horde_Image_ImagickProxy($size['width'] + $this->_params['borderwidth'],
                                                $size['height'] + $this->_params['borderwidth'],
                                                $this->_params['bordercolor'],
                                                $this->_image->_type);
            $return->clear();
            $return->readImageBlob($new->raw());
            return $return;
        } else {
            $size = $image->getDimensions();
            $params = array('temp' => $this->_image->_tmpdir,
                            'data' => $image->raw());
            $new = Horde_Image::factory('im', $params);
            $new->addEffect('round_corners', array('border' => 2, 'bordercolor' => '#111', 'background' => 'none'));
            $new->applyEffects();
            return $new->toFile();
        }
    }

}
