/* This compressed file is part of Xinha. For uncompressed sources, forum, and bug reports, go to xinha.org */
/* This file is part of version 0.95 released Mon, 12 May 2008 17:33:15 +0200 */
/* The URL of the most recent version of this file is http://svn.xinha.webfactional.com/trunk/modules/InsertImage/insert_image.js */
InsertImage._pluginInfo={name:"InsertImage",origin:"Xinha Core",version:"$LastChangedRevision:992 $".replace(/^[^:]*:\s*(.*)\s*\$$/,"$1"),developer:"The Xinha Core Developer Team",developer_url:"$HeadURL:http://svn.xinha.webfactional.com/trunk/modules/InsertImage/insert_image.js $".replace(/^[^:]*:\s*(.*)\s*\$$/,"$1"),sponsor:"",sponsor_url:"",license:"htmlArea"};
function InsertImage(_1){
}
Xinha.prototype._insertImage=function(_2){
var _3=this;
var _4;
if(typeof _2=="undefined"){
_2=this.getParentElement();
if(_2&&_2.tagName.toLowerCase()!="img"){
_2=null;
}
}
var _5;
if(typeof _3.config.baseHref!="undefined"&&_3.config.baseHref!==null){
_5=_3.config.baseHref;
}else{
var _6=window.location.toString().split("/");
_6.pop();
_5=_6.join("/");
}
if(_2){
function getSpecifiedAttribute(_7,_8){
var a=_7.attributes;
for(var i=0;i<a.length;i++){
if(a[i].nodeName==_8&&a[i].specified){
return a[i].value;
}
}
return "";
}
_4={f_base:_5,f_url:this.stripBaseURL(_2.getAttribute("src",2)),f_alt:_2.alt,f_border:_2.border,f_align:_2.align,f_vert:getSpecifiedAttribute(_2,"vspace"),f_horiz:getSpecifiedAttribute(_2,"hspace"),f_width:_2.width,f_height:_2.height};
}else{
_4={f_base:_5,f_url:""};
}
Dialog(_3.config.URIs.insert_image,function(_b){
if(!_b){
return false;
}
var _c=_2;
if(!_c){
if(Xinha.is_ie){
var _d=_3.getSelection();
var _e=_3.createRange(_d);
_3._doc.execCommand("insertimage",false,_b.f_url);
_c=_e.parentElement();
if(_c.tagName.toLowerCase()!="img"){
_c=_c.previousSibling;
}
}else{
_c=document.createElement("img");
_c.src=_b.f_url;
_3.insertNodeAtSelection(_c);
if(!_c.tagName){
_c=_e.startContainer.firstChild;
}
}
}else{
_c.src=_b.f_url;
}
for(var _f in _b){
var _10=_b[_f];
switch(_f){
case "f_alt":
if(_10){
_c.alt=_10;
}else{
_c.removeAttribute("alt");
}
break;
case "f_border":
if(_10){
_c.border=parseInt(_10||"0");
}else{
_c.removeAttribute("border");
}
break;
case "f_align":
if(_10){
_c.align=_10;
}else{
_c.removeAttribute("align");
}
break;
case "f_vert":
if(_10!=""){
_c.vspace=parseInt(_10||"0");
}else{
_c.removeAttribute("vspace");
}
break;
case "f_horiz":
if(_10!=""){
_c.hspace=parseInt(_10||"0");
}else{
_c.removeAttribute("hspace");
}
break;
case "f_width":
if(_10){
_c.width=parseInt(_10||"0");
}else{
_c.removeAttribute("width");
}
break;
case "f_height":
if(_10){
_c.height=parseInt(_10||"0");
}else{
_c.removeAttribute("height");
}
break;
}
}
},_4);
};

