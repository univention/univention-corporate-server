/**
 * SPDX-License-Identifier: AGPL-3.0-only
 * SPDX-FileCopyrightText: 2023-2024 Univention GmbH
 */

import { Meta, StoryFn } from '@storybook/vue3';

import { reactive } from 'vue';
import { NodeProps } from '../../src/components/widgets/Tree/types';
import Tree from '../../src/components/widgets/Tree/Tree.vue';

export default {
  title: 'Widgets/Tree',
  component: Tree,
} as Meta<typeof Tree>;

const rootNode: NodeProps = {
  id: 'dc=demo,dc=univention,dc=de',
  label: 'demo.univention.de:/',
  icon: 'udm-container-dc',
  path: 'demo.univention.de:/',
  objectType: 'container/dc',
  $operations$: ['search', 'edit'],
  $flags$: [],
  $childs$: true,
  $isSuperordinate$: false,
};

const treeNodes: NodeProps[] = [
  {
    id: 'cn=univention,dc=demo,dc=univention,dc=de',
    label: 'univention',
    icon: 'udm-settings-cn',
    path: 'demo.univention.de:/univention',
    objectType: 'settings/cn',
    $operations$: ['search'],
    $flags$: [],
    $childs$: true,
    $isSuperordinate$: true,
  },
  {
    id: 'cn=mail,dc=demo,dc=univention,dc=de',
    label: 'mail',
    icon: 'udm-container-cn',
    path: 'demo.univention.de:/mail',
    objectType: 'container/cn',
    $operations$: ['add', 'edit', 'remove', 'search', 'move', 'subtree_move'],
    $flags$: [],
    $childs$: true,
    $isSuperordinate$: false,
  },
  {
    id: 'cn=kerberos,dc=demo,dc=univention,dc=de',
    label: 'kerberos',
    icon: 'udm-container-cn',
    path: 'demo.univention.de:/kerberos',
    objectType: 'container/cn',
    $operations$: ['add', 'edit', 'remove', 'search', 'move', 'subtree_move'],
    $flags$: [],
    $childs$: true,
    $isSuperordinate$: false,
  },
  {
    id: 'cn=computers,dc=demo,dc=univention,dc=de',
    label: 'computers',
    icon: 'udm-container-cn',
    path: 'demo.univention.de:/computers',
    objectType: 'container/cn',
    $operations$: ['add', 'edit', 'remove', 'search', 'move', 'subtree_move'],
    $flags$: [],
    $childs$: true,
    $isSuperordinate$: false,
  },
  {
    id: 'cn=printers,dc=demo,dc=univention,dc=de',
    label: 'printers',
    icon: 'udm-container-cn',
    path: 'demo.univention.de:/printers',
    objectType: 'container/cn',
    $operations$: ['add', 'edit', 'remove', 'search', 'move', 'subtree_move'],
    $flags$: [],
    $childs$: true,
    $isSuperordinate$: false,
  },
];

const computerNodes: NodeProps[] = [{
  id: 'cn=dc,cn=computers,dc=demo,dc=univention,dc=de',
  label: 'dc',
  icon: 'udm-container-cn',
  path: 'demo.univention.de:/computers/dc',
  objectType: 'container/cn',
  $operations$: [
    'add',
    'edit',
    'remove',
    'search',
    'move',
    'subtree_move',
  ],
  $flags$: [],
  $childs$: true,
  $isSuperordinate$: false,
},
{
  id: 'cn=memberserver,cn=computers,dc=demo,dc=univention,dc=de',
  label: 'memberserver',
  icon: 'udm-container-cn',
  path: 'demo.univention.de:/computers/memberserver',
  objectType: 'container/cn',
  $operations$: [
    'add',
    'edit',
    'remove',
    'search',
    'move',
    'subtree_move',
  ],
  $flags$: [],
  $childs$: true,
  $isSuperordinate$: false,
}];

const mailNodes: NodeProps[] = [{
  id: 'cn=domain,cn=mail,dc=demo,dc=univention,dc=de',
  label: 'domain',
  icon: 'udm-container-cn',
  path: 'demo.univention.de:/mail/domain',
  objectType: 'container/cn',
  $operations$: [
    'add',
    'edit',
    'remove',
    'search',
    'move',
    'subtree_move',
  ],
  $flags$: [],
  $childs$: true,
  $isSuperordinate$: false,
},
{
  id: 'cn=folder,cn=mail,dc=demo,dc=univention,dc=de',
  label: 'folder',
  icon: 'udm-container-cn',
  path: 'demo.univention.de:/mail/folder',
  objectType: 'container/cn',
  $operations$: [
    'add',
    'edit',
    'remove',
    'search',
    'move',
    'subtree_move',
  ],
  $flags$: [],
  $childs$: true,
  $isSuperordinate$: false,
},
{
  id: 'cn=mailinglists,cn=mail,dc=demo,dc=univention,dc=de',
  label: 'mailinglists',
  icon: 'udm-container-cn',
  path: 'demo.univention.de:/mail/mailinglists',
  objectType: 'container/cn',
  $operations$: [
    'add',
    'edit',
    'remove',
    'search',
    'move',
    'subtree_move',
  ],
  $flags$: [],
  $childs$: true,
  $isSuperordinate$: false,
}];

const Template: StoryFn<typeof Tree> = (args) => ({
  components: { Tree },
  setup() {
    const data = reactive(args);

    // mock fetch data from server
    async function fetchNodeChildren(node: NodeProps): Promise<NodeProps[]> {
      const randomTimeResponse = Math.floor(Math.random() * 1000) + 500;
      return new Promise((resolve) => {
        setTimeout(() => {
          if (node.id === 'cn=computers,dc=demo,dc=univention,dc=de') {
            resolve(computerNodes);
          } else if (node.id === 'cn=mail,dc=demo,dc=univention,dc=de') {
            resolve(mailNodes);
          } else if (node.id === 'dc=demo,dc=univention,dc=de') {
            resolve(treeNodes);
          } else {
            resolve([]);
          }
        }, randomTimeResponse);
      });
    }

    async function onExpand(expandedNode: NodeProps) {
      data.isLoading = true;
      const children = await fetchNodeChildren(expandedNode);
      data.lists = [...data.lists, ...children];
      if (children.length === 0) {
        expandedNode.$childs$ = false;
      }
      data.isLoading = false;
    }

    async function onCollapse(collapsedNode: NodeProps) {
      // remove children from tree
      data.lists = data.lists.filter((node: NodeProps) => {
        if (node.id === collapsedNode.id || !node.id.includes(collapsedNode.id)) return true;
        return false;
      });
    }

    async function onRemove(deletedNode: NodeProps) {
      // remove node & children of deleted node from tree
      data.lists = data.lists.filter((node: NodeProps) => !node.id.includes(deletedNode.id));
    }

    async function onReload() {
      await onCollapse(rootNode);
      await onExpand(rootNode);
    }

    data.onExpand = onExpand;
    data.onCollapse = onCollapse;
    data.onRemove = onRemove;
    data.onReload = onReload;
    return { data };
  },
  template: `<div>
    <Tree v-bind="data">
      <template #context-menu-option-edit="{option}">
      </template>
    </Tree>
  </div>`,
});

export const Default = Template.bind({});
Default.args = {
  name: 'tree',
  lists: [rootNode],
  isLoading: false,
  isContextMenuDisabled: false,
  onExpand: (node: NodeProps) => {
    console.log('onExpand', node);
  },
  onCollapse: (node: NodeProps) => {
    console.log('onCollapse', node);
  },
  onSelect: (node: NodeProps) => {
    console.log('onSelect', node);
  },

  // all operation methods:
  on: {
    edit: (node: NodeProps) => {
      console.log('onEdit', node);
    },
    remove: (node: NodeProps) => {
      console.log('onRemove', node);
    },
    move: (node: NodeProps) => {
      console.log('onMove', node);
    },
    search: (node: NodeProps) => {
      console.log('onSearch', node);
    },
    add: (node: NodeProps) => {
      console.log('onAdd', node);
    },
    reload: (node: NodeProps) => {
      console.log('onReload', node);
    },
  },
  contextMenuOptions: [
    { icon: 'edit', label: 'Edit', operation: 'edit' },
    { icon: 'trash', label: 'Delete', operation: 'remove' },
    { icon: '', label: 'Move to...', operation: 'move' },
    { icon: 'refresh-cw', label: 'Reload', operation: 'reload' },
  ],
};
