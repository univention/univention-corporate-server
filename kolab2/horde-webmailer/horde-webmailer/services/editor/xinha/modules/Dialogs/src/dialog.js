/* This compressed file is part of Xinha. For uncompressed sources, forum, and bug reports, go to xinha.org */
/* This file is part of version 0.95 released Mon, 12 May 2008 17:33:15 +0200 */
/* The URL of the most recent version of this file is http://svn.xinha.webfactional.com/trunk/modules/Dialogs/dialog.js */
function Dialog(_1,_2,_3){
if(typeof _3=="undefined"){
_3=window;
}
if(typeof window.showModalDialog=="function"&&!Xinha.is_webkit){
Dialog._return=function(_4){
if(typeof _2=="function"){
_2(_4);
}
};
var r=window.showModalDialog(_1,_3,"dialogheight=300;dialogwidth=400;resizable=yes");
}else{
Dialog._geckoOpenModal(_1,_2,_3);
}
}
Dialog._parentEvent=function(ev){
setTimeout(function(){
if(Dialog._modal&&!Dialog._modal.closed){
Dialog._modal.focus();
}
},50);
try{
if(Dialog._modal&&!Dialog._modal.closed){
Xinha._stopEvent(ev);
}
}
catch(e){
}
};
Dialog._return=null;
Dialog._modal=null;
Dialog._arguments=null;
Dialog._selection=null;
Dialog._geckoOpenModal=function(_7,_8,_9){
var _a=window.open(_7,"hadialog","toolbar=no,menubar=no,personalbar=no,width=10,height=10,"+"scrollbars=no,resizable=yes,modal=yes,dependable=yes");
Dialog._modal=_a;
Dialog._arguments=_9;
function capwin(w){
Xinha._addEvent(w,"click",Dialog._parentEvent);
Xinha._addEvent(w,"mousedown",Dialog._parentEvent);
Xinha._addEvent(w,"focus",Dialog._parentEvent);
}
function relwin(w){
Xinha._removeEvent(w,"click",Dialog._parentEvent);
Xinha._removeEvent(w,"mousedown",Dialog._parentEvent);
Xinha._removeEvent(w,"focus",Dialog._parentEvent);
}
capwin(window);
for(var i=0;i<window.frames.length;i++){
try{
capwin(window.frames[i]);
}
catch(e){
}
}
Dialog._return=function(_e){
if(_e&&_8){
_8(_e);
}
relwin(window);
for(var i=0;i<window.frames.length;i++){
try{
relwin(window.frames[i]);
}
catch(e){
}
}
Dialog._modal=null;
};
Dialog._modal.focus();
};

