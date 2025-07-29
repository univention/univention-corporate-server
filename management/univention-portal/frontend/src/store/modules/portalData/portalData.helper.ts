/*
 * SPDX-FileCopyrightText: 2021-2025 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */
import vm from '@/main';
import _ from '@/jsHelper/translate';
import { Position } from '@/store/modules/portalData/portalData.models';

export default function setScreenReaderAccouncement(fromPosition: Position, toPosition: Position, getPortalLayout, setMessage): void {
  const categoryPositionBefore = fromPosition.categoryIdx;
  const categoryPositionAfter = toPosition.categoryIdx;
  const tilePositionBefore = fromPosition.entryIdx;
  const tilePositionAfter = toPosition.entryIdx;
  if (categoryPositionBefore && (tilePositionBefore !== null) && (tilePositionAfter !== null) && (categoryPositionAfter !== null)) {
    const numberOfTiles = getPortalLayout[categoryPositionAfter].tiles.length;
    const newPositionInArray = tilePositionAfter + 1;
    const titleOfCategory = getPortalLayout[categoryPositionAfter].title;

    if (fromPosition.categoryIdx !== toPosition.categoryIdx) {
      setMessage(_('Tile moved into category %(category)s', {
        category: vm.$localized(titleOfCategory),
      }));
    } else if (fromPosition.contextType === 'category') {
      setMessage(_('Tile moved into position %(positionInArray)s of %(numberOfTiles)s', {
        positionInArray: newPositionInArray.toString(),
        numberOfTiles: numberOfTiles.toString(),
      }));
    } else if (fromPosition.contextType === 'folder') {
      const folderIndex = fromPosition.folderIdx ? fromPosition.folderIdx : -1;
      const numberOfTilesInFolder = getPortalLayout[categoryPositionBefore].tiles[folderIndex].tiles.length;
      setMessage(_('Tile in Folder moved into position %(newPositionInArray)s of %(numberOfTilesInFolder)s', {
        newPositionInArray: newPositionInArray.toString(),
        numberOfTilesInFolder: numberOfTilesInFolder.toString(),
      }));
    }
  }
  if (fromPosition.contextType === 'root') {
    if (fromPosition.entryIdx && toPosition.entryIdx) {
      const newCategoryPosition = toPosition.entryIdx;
      const numberOfCategories = getPortalLayout.filter((category) => (!category.dn.includes('$$menu$$') && !category.dn.includes('$$user$$') && !category.dn.includes('cn=new'))).length;
      setMessage(_('Category moved to position %(newCategoryPosition)s of %(numberOfCategories)s', {
        newCategoryPosition: newCategoryPosition.toString(),
        numberOfCategories: numberOfCategories.toString(),
      }));
    }
  }

  if (fromPosition.contextType === 'folder' && !categoryPositionBefore) {
    // TODO Setmessage for Folder in Menu
  }
}
