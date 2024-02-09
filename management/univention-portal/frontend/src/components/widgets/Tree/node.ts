/**
 * SPDX-License-Identifier: AGPL-3.0-only
 * SPDX-FileCopyrightText: 2023-2024 Univention GmbH
 */

import { NodeProps } from './types';

class Node {
  public parent: Node | null = null;

  public children: Node[] = [];

  public data: NodeProps;

  public isSelected = false;

  public isExpanded = false;

  constructor(data: NodeProps, parent: Node | null, children: Node[], isSelected = false, isExpanded = false) {
    this.data = data;
    this.parent = parent;
    this.children = children;
    this.isSelected = isSelected;
    this.isExpanded = isExpanded;
  }

  get level(): number {
    let level = 1;
    const nodePath = this.data.path.split('/');
    // check the root node (all nodes always have at least two elements)
    // but the in the second element of the root node is always empty
    if (nodePath.length > 1 && nodePath[1] === '') {
      return level;
    }

    level = nodePath.length;
    return level;
  }

  get parentPath(): string | null {
    // if the node is the root node, it has no parent
    if (this.level === 1) return null;
    const nodePath = this.data.path.split('/');
    nodePath.pop();
    const parentPath = `${nodePath.join('/')}`;
    // if this node is the node below the root node, the parent path always has the '/' at the end
    if (this.level === 2) return `${parentPath}/`;
    return parentPath;
  }

  public toggleIsSelected(isSelected?: boolean): void {
    this.isSelected = isSelected ?? !this.isSelected;
  }

  public toggleIsExpanded(isExpanded?: boolean): void {
    this.isExpanded = isExpanded ?? !this.isExpanded;
  }
}

export default Node;
