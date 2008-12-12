<?php

abstract class DojoBlock
{
  protected $package;
  public $start;
  public $end;

  public function __construct($package, $line_number = false, $position = false){
    $this->package = $package;
    if($line_number !== false && $position !== false){
      $this->setStart($line_number, $position);
    }
  }
  
  public function setStart($line_number, $position){
    $this->start = array($line_number, $position);
  }
  
  protected function setEnd($line_number, $position){
      $this->end = array($line_number, $position);
  }
  
  public abstract function build();
}

?>