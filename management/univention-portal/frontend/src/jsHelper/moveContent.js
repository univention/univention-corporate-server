/*
 * Copyright 2021 Univention GmbH
 *
 * https://www.univention.de/
 *
 * All rights reserved.
 *
 * The source code of this program is made available
 * under the terms of the GNU Affero General Public License version 3
 * (GNU AGPL V3) as published by the Free Software Foundation.
 *
 * Binary versions of this program provided by Univention to you as
 * well as other copyrighted, protected or trademarked materials like
 * Logos, graphics, fonts, specific documentations and configurations,
 * cryptographic keys etc. are subject to a license agreement between
 * you and Univention and not subject to the GNU AGPL V3.
 *
 * In the case you use this program under the terms of the GNU AGPL V3,
 * the program is provided in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public
 * License with the Debian GNU/Linux or Univention distribution in file
 * /usr/share/common-licenses/AGPL-3; if not, see
 * <https://www.gnu.org/licenses/>.
 */
const moveContentHelper = (moveableElement) => {
  // check for possible datalist elements
  const dataLists = document.querySelector('datalist');
  let datalistId = '';

  let elem = '';
  let pos1 = 0;
  let pos2 = 0;
  let pos3 = 0;
  let pos4 = 0;

  // store original datalist id if available
  if (dataLists) {
    datalistId = dataLists.id;
  }

  const enableDatalist = () => {
    if (dataLists) {
      dataLists.id = datalistId;
    }
  };

  const disableDatalist = () => {
    if (dataLists) {
      dataLists.id = '';
    }
  };

  const closeDragElement = () => {
    // stop moving when mouse button is released
    document.onmouseup = null;
    document.onmousemove = null;
  };

  const elementDrag = (e) => {
    e.preventDefault();

    // disable datalist element options while dragging
    disableDatalist();

    // calculate the new cursor position
    pos1 = pos3 - e.clientX;
    pos2 = pos4 - e.clientY;
    pos3 = e.clientX;
    pos4 = e.clientY;

    // set the element's new position
    elem.style.top = `${elem.offsetTop - pos2}px`;
    elem.style.left = `${elem.offsetLeft - pos1}px`;

    // enable datalist element options
    enableDatalist();
  };

  const dragMouseDown = (e) => {
    e.preventDefault();
    // get the mouse cursor position at startup
    pos3 = e.clientX;
    pos4 = e.clientY;
    document.onmouseup = closeDragElement;
    // disable datalist element options while dragging
    disableDatalist();

    // call a function whenever the cursor moves
    document.onmousemove = elementDrag;

    // enable datalist element options
    enableDatalist();
  };

  if (moveableElement && moveableElement.value) {
    elem = moveableElement.value;
    elem.onmousedown = dragMouseDown;
  }
};

export default moveContentHelper;
