/* This compressed file is part of Xinha. For uncompressed sources, forum, and bug reports, go to xinha.org */
/* This file is part of version 0.95 released Mon, 12 May 2008 17:33:15 +0200 */
/* The URL of the most recent version of this file is http://svn.xinha.webfactional.com/trunk/plugins/ContextMenu/context-menu.js */
Xinha.loadStyle("menu.css","ContextMenu");
function ContextMenu(_1){
this.editor=_1;
}
ContextMenu._pluginInfo={name:"ContextMenu",version:"1.0",developer:"Mihai Bazon",developer_url:"http://dynarch.com/mishoo/",c_owner:"dynarch.com",sponsor:"American Bible Society",sponsor_url:"http://www.americanbible.org",license:"htmlArea"};
Xinha.Config.prototype.ContextMenu={disableMozillaSpellCheck:false};
ContextMenu.prototype.onGenerate=function(){
var _2=this;
var _3=this.editordoc=this.editor._iframe.contentWindow.document;
Xinha._addEvents(_3,["contextmenu"],function(_4){
return _2.popupMenu(Xinha.is_ie?_2.editor._iframe.contentWindow.event:_4);
});
this.currentMenu=null;
if(this.editor.config.ContextMenu.disableMozillaSpellCheck){
this.editordoc.body.spellcheck=false;
}
};
ContextMenu.prototype.getContextMenu=function(_5){
var _6=this;
var _7=this.editor;
var _8=_7.config;
var _9=[];
var _a=this.editor.plugins.TableOperations;
if(_a){
_a=_a.instance;
}
var _b=_7.hasSelectedText();
if(!Xinha.is_gecko){
if(_b){
_9.push([Xinha._lc("Cut","ContextMenu"),function(){
_7.execCommand("cut");
},null,_8.btnList["cut"][1]],[Xinha._lc("Copy","ContextMenu"),function(){
_7.execCommand("copy");
},null,_8.btnList["copy"][1]]);
_9.push([Xinha._lc("Paste","ContextMenu"),function(){
_7.execCommand("paste");
},null,_8.btnList["paste"][1]]);
}
}
var _c=_5;
var _d=[];
var _e=null;
var _f=null;
var tr=null;
var td=null;
var img=null;
function tableOperation(_13){
_a.buttonPress(_7,_13);
}
function insertPara(_14){
var el=_c;
var par=el.parentNode;
var p=_7._doc.createElement("p");
p.appendChild(_7._doc.createElement("br"));
par.insertBefore(p,_14?el.nextSibling:el);
var sel=_7._getSelection();
var _19=_7._createRange(sel);
if(!Xinha.is_ie){
sel.removeAllRanges();
_19.selectNodeContents(p);
_19.collapse(true);
sel.addRange(_19);
}else{
_19.moveToElementText(p);
_19.collapse(true);
_19.select();
}
}
for(;_5;_5=_5.parentNode){
var tag=_5.tagName;
if(!tag){
continue;
}
tag=tag.toLowerCase();
switch(tag){
case "img":
img=_5;
_d.push(null,[Xinha._lc("_Image Properties...","ContextMenu"),function(){
_7._insertImage(img);
},Xinha._lc("Show the image properties dialog","ContextMenu"),_8.btnList["insertimage"][1]]);
break;
case "a":
_e=_5;
_d.push(null,[Xinha._lc("_Modify Link...","ContextMenu"),function(){
_7.config.btnList["createlink"][3](_7);
},Xinha._lc("Current URL is","ContextMenu")+": "+_e.href,_8.btnList["createlink"][1]],[Xinha._lc("Chec_k Link...","ContextMenu"),function(){
window.open(_e.href);
},Xinha._lc("Opens this link in a new window","ContextMenu")],[Xinha._lc("_Remove Link...","ContextMenu"),function(){
if(confirm(Xinha._lc("Please confirm that you want to unlink this element.","ContextMenu")+"\n"+Xinha._lc("Link points to:","ContextMenu")+" "+_e.href)){
while(_e.firstChild){
_e.parentNode.insertBefore(_e.firstChild,_e);
}
_e.parentNode.removeChild(_e);
}
},Xinha._lc("Unlink the current element","ContextMenu")]);
break;
case "td":
td=_5;
if(!_a){
break;
}
_d.push(null,[Xinha._lc("C_ell Properties...","ContextMenu"),function(){
tableOperation("TO-cell-prop");
},Xinha._lc("Show the Table Cell Properties dialog","ContextMenu"),_8.btnList["TO-cell-prop"][1]],[Xinha._lc("Insert Cell After","ContextMenu"),function(){
tableOperation("TO-cell-insert-after");
},Xinha._lc("Insert Cell After","ContextMenu"),_8.btnList["TO-cell-insert-after"][1]],[Xinha._lc("Insert Cell Before","ContextMenu"),function(){
tableOperation("TO-cell-insert-before");
},Xinha._lc("Insert Cell After","ContextMenu"),_8.btnList["TO-cell-insert-before"][1]],[Xinha._lc("Delete Cell","ContextMenu"),function(){
tableOperation("TO-cell-delete");
},Xinha._lc("Delete Cell","ContextMenu"),_8.btnList["TO-cell-delete"][1]],[Xinha._lc("Merge Cells","ContextMenu"),function(){
tableOperation("TO-cell-merge");
},Xinha._lc("Merge Cells","ContextMenu"),_8.btnList["TO-cell-merge"][1]]);
break;
case "tr":
tr=_5;
if(!_a){
break;
}
_d.push(null,[Xinha._lc("Ro_w Properties...","ContextMenu"),function(){
tableOperation("TO-row-prop");
},Xinha._lc("Show the Table Row Properties dialog","ContextMenu"),_8.btnList["TO-row-prop"][1]],[Xinha._lc("I_nsert Row Before","ContextMenu"),function(){
tableOperation("TO-row-insert-above");
},Xinha._lc("Insert a new row before the current one","ContextMenu"),_8.btnList["TO-row-insert-above"][1]],[Xinha._lc("In_sert Row After","ContextMenu"),function(){
tableOperation("TO-row-insert-under");
},Xinha._lc("Insert a new row after the current one","ContextMenu"),_8.btnList["TO-row-insert-under"][1]],[Xinha._lc("_Delete Row","ContextMenu"),function(){
tableOperation("TO-row-delete");
},Xinha._lc("Delete the current row","ContextMenu"),_8.btnList["TO-row-delete"][1]]);
break;
case "table":
_f=_5;
if(!_a){
break;
}
_d.push(null,[Xinha._lc("_Table Properties...","ContextMenu"),function(){
tableOperation("TO-table-prop");
},Xinha._lc("Show the Table Properties dialog","ContextMenu"),_8.btnList["TO-table-prop"][1]],[Xinha._lc("Insert _Column Before","ContextMenu"),function(){
tableOperation("TO-col-insert-before");
},Xinha._lc("Insert a new column before the current one","ContextMenu"),_8.btnList["TO-col-insert-before"][1]],[Xinha._lc("Insert C_olumn After","ContextMenu"),function(){
tableOperation("TO-col-insert-after");
},Xinha._lc("Insert a new column after the current one","ContextMenu"),_8.btnList["TO-col-insert-after"][1]],[Xinha._lc("De_lete Column","ContextMenu"),function(){
tableOperation("TO-col-delete");
},Xinha._lc("Delete the current column","ContextMenu"),_8.btnList["TO-col-delete"][1]]);
break;
case "body":
_d.push(null,[Xinha._lc("Justify Left","ContextMenu"),function(){
_7.execCommand("justifyleft");
},null,_8.btnList["justifyleft"][1]],[Xinha._lc("Justify Center","ContextMenu"),function(){
_7.execCommand("justifycenter");
},null,_8.btnList["justifycenter"][1]],[Xinha._lc("Justify Right","ContextMenu"),function(){
_7.execCommand("justifyright");
},null,_8.btnList["justifyright"][1]],[Xinha._lc("Justify Full","ContextMenu"),function(){
_7.execCommand("justifyfull");
},null,_8.btnList["justifyfull"][1]]);
break;
}
}
if(_b&&!_e){
_9.push(null,[Xinha._lc("Make lin_k...","ContextMenu"),function(){
_7.config.btnList["createlink"][3](_7);
},Xinha._lc("Create a link","ContextMenu"),_8.btnList["createlink"][1]]);
}
for(var i=0;i<_d.length;++i){
_9.push(_d[i]);
}
if(!/html|body/i.test(_c.tagName)){
_9.push(null,[Xinha._lc({string:"Remove the $elem Element...",replace:{elem:"&lt;"+_c.tagName+"&gt;"}},"ContextMenu"),function(){
if(confirm(Xinha._lc("Please confirm that you want to remove this element:","ContextMenu")+" "+_c.tagName)){
var el=_c;
var p=el.parentNode;
p.removeChild(el);
if(Xinha.is_gecko){
if(p.tagName.toLowerCase()=="td"&&!p.hasChildNodes()){
p.appendChild(_7._doc.createElement("br"));
}
_7.forceRedraw();
_7.focusEditor();
_7.updateToolbar();
if(_f){
var _1e=_f.style.borderCollapse;
_f.style.borderCollapse="collapse";
_f.style.borderCollapse="separate";
_f.style.borderCollapse=_1e;
}
}
}
},Xinha._lc("Remove this node from the document","ContextMenu")],[Xinha._lc("Insert paragraph before","ContextMenu"),function(){
insertPara(false);
},Xinha._lc("Insert a paragraph before the current node","ContextMenu")],[Xinha._lc("Insert paragraph after","ContextMenu"),function(){
insertPara(true);
},Xinha._lc("Insert a paragraph after the current node","ContextMenu")]);
}
if(!_9[0]){
_9.shift();
}
return _9;
};
ContextMenu.prototype.popupMenu=function(ev){
var _20=this;
if(this.currentMenu){
this.closeMenu();
}
function getPos(el){
var r={x:el.offsetLeft,y:el.offsetTop};
if(el.offsetParent){
var tmp=getPos(el.offsetParent);
r.x+=tmp.x;
r.y+=tmp.y;
}
return r;
}
function documentClick(ev){
ev||(ev=window.event);
if(!_20.currentMenu){
alert(Xinha._lc("How did you get here? (Please report!)","ContextMenu"));
return false;
}
var el=Xinha.is_ie?ev.srcElement:ev.target;
for(;el!=null&&el!=_20.currentMenu;el=el.parentNode){
}
if(el==null){
_20.closeMenu();
}
}
var _26=[];
function keyPress(ev){
ev||(ev=window.event);
Xinha._stopEvent(ev);
if(ev.keyCode==27){
_20.closeMenu();
return false;
}
var key=String.fromCharCode(Xinha.is_ie?ev.keyCode:ev.charCode).toLowerCase();
for(var i=_26.length;--i>=0;){
var k=_26[i];
if(k[0].toLowerCase()==key){
k[1].__msh.activate();
}
}
}
_20.closeMenu=function(){
_20.currentMenu.parentNode.removeChild(_20.currentMenu);
_20.currentMenu=null;
Xinha._removeEvent(document,"mousedown",documentClick);
Xinha._removeEvent(_20.editordoc,"mousedown",documentClick);
if(_26.length>0){
Xinha._removeEvent(_20.editordoc,"keypress",keyPress);
}
if(Xinha.is_ie){
_20.iePopup.hide();
}
};
var _2b=Xinha.is_ie?ev.srcElement:ev.target;
var _2c=getPos(_20.editor._htmlArea);
var x=ev.clientX+_2c.x;
var y=ev.clientY+_2c.y;
var div;
var doc;
if(!Xinha.is_ie){
doc=document;
}else{
var _31=this.iePopup=window.createPopup();
doc=_31.document;
doc.open();
doc.write("<html><head><style type='text/css'>@import url("+Xinha.getPluginDir("ContextMenu")+"/menu.css); html, body { padding: 0px; margin: 0px; overflow: hidden; border: 0px; }</style></head><body unselectable='yes'></body></html>");
doc.close();
}
div=doc.createElement("div");
if(Xinha.is_ie){
div.unselectable="on";
}
div.oncontextmenu=function(){
return false;
};
div.className="htmlarea-context-menu";
if(!Xinha.is_ie){
div.style.left=div.style.top="0px";
}
doc.body.appendChild(div);
var _32=doc.createElement("table");
div.appendChild(_32);
_32.cellSpacing=0;
_32.cellPadding=0;
var _33=doc.createElement("tbody");
_32.appendChild(_33);
var _34=this.getContextMenu(_2b);
for(var i=0;i<_34.length;++i){
var _36=_34[i];
var _37=doc.createElement("tr");
_33.appendChild(_37);
if(Xinha.is_ie){
_37.unselectable="on";
}else{
_37.onmousedown=function(ev){
Xinha._stopEvent(ev);
return false;
};
}
if(!_36){
_37.className="separator";
var td=doc.createElement("td");
td.className="icon";
var _3a=">";
if(Xinha.is_ie){
td.unselectable="on";
_3a=" unselectable='on' style='height=1px'>&nbsp;";
}
td.innerHTML="<div"+_3a+"</div>";
var td1=td.cloneNode(true);
td1.className="label";
_37.appendChild(td);
_37.appendChild(td1);
}else{
var _3c=_36[0];
_37.className="item";
_37.__msh={item:_37,label:_3c,action:_36[1],tooltip:_36[2]||null,icon:_36[3]||null,activate:function(){
_20.closeMenu();
_20.editor.focusEditor();
this.action();
}};
_3c=_3c.replace(/_([a-zA-Z0-9])/,"<u>$1</u>");
if(_3c!=_36[0]){
_26.push([RegExp.$1,_37]);
}
_3c=_3c.replace(/__/,"_");
var td1=doc.createElement("td");
if(Xinha.is_ie){
td1.unselectable="on";
}
_37.appendChild(td1);
td1.className="icon";
if(_37.__msh.icon){
var t=Xinha.makeBtnImg(_37.__msh.icon,doc);
td1.appendChild(t);
}
var td2=doc.createElement("td");
if(Xinha.is_ie){
td2.unselectable="on";
}
_37.appendChild(td2);
td2.className="label";
td2.innerHTML=_3c;
_37.onmouseover=function(){
this.className+=" hover";
_20.editor._statusBarTree.innerHTML=this.__msh.tooltip||"&nbsp;";
};
_37.onmouseout=function(){
this.className="item";
};
_37.oncontextmenu=function(ev){
this.__msh.activate();
if(!Xinha.is_ie){
Xinha._stopEvent(ev);
}
return false;
};
_37.onmouseup=function(ev){
var _41=(new Date()).getTime();
if(_41-_20.timeStamp>500){
this.__msh.activate();
}
if(!Xinha.is_ie){
Xinha._stopEvent(ev);
}
return false;
};
}
}
if(!Xinha.is_ie){
div.style.left=x+"px";
div.style.top=y+"px";
}else{
this.iePopup.show(ev.screenX,ev.screenY,300,50);
var w=div.offsetWidth;
var h=div.offsetHeight;
this.iePopup.show(ev.screenX,ev.screenY,w,h);
}
this.currentMenu=div;
this.timeStamp=(new Date()).getTime();
Xinha._addEvent(document,"mousedown",documentClick);
Xinha._addEvent(this.editordoc,"mousedown",documentClick);
if(_26.length>0){
Xinha._addEvent(this.editordoc,"keypress",keyPress);
}
Xinha._stopEvent(ev);
return false;
};

