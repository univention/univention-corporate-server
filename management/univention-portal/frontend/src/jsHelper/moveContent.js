const moveContentHelper = (moveableElement) => {
  let elem = '';
  let pos1 = 0;
  let pos2 = 0;
  let pos3 = 0;
  let pos4 = 0;

  const closeDragElement = () => {
    // stop moving when mouse button is released
    document.onmouseup = null;
    document.onmousemove = null;
  };

  const elementDrag = (e) => {
    e.preventDefault();
    // calculate the new cursor position
    pos1 = pos3 - e.clientX;
    pos2 = pos4 - e.clientY;
    pos3 = e.clientX;
    pos4 = e.clientY;
    // set the element's new position
    elem.style.top = `${elem.offsetTop - pos2}px`;
    elem.style.left = `${elem.offsetLeft - pos1}px`;
  };

  const dragMouseDown = (e) => {
    e.preventDefault();
    // get the mouse cursor position at startup
    pos3 = e.clientX;
    pos4 = e.clientY;
    document.onmouseup = closeDragElement;
    // call a function whenever the cursor moves
    document.onmousemove = elementDrag;
  };

  if (moveableElement && moveableElement.value) {
    elem = moveableElement.value;
    elem.onmousedown = dragMouseDown;
  }
};

export default moveContentHelper;
