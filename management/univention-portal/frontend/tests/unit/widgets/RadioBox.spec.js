/**
  Copyright 2021 Univention GmbH

  https://www.univention.de/

  All rights reserved.

  The source code of this program is made available
  under the terms of the GNU Affero General Public License version 3
  (GNU AGPL V3) as published by the Free Software Foundation.

  Binary versions of this program provided by Univention to you as
  well as other copyrighted, protected or trademarked materials like
  Logos, graphics, fonts, specific documentations and configurations,
  cryptographic keys etc. are subject to a license agreement between
  you and Univention and not subject to the GNU AGPL V3.

  In the case you use this program under the terms of the GNU AGPL V3,
  the program is provided in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
  GNU Affero General Public License for more details.

  You should have received a copy of the GNU Affero General Public
  License with the Debian GNU/Linux or Univention distribution in file
  /usr/share/common-licenses/AGPL-3; if not, see
  <https://www.gnu.org/licenses/>.
* */

import { mount } from '@vue/test-utils';

import RadioBox from '@/components/widgets/RadioBox.vue';

const radioBoxName = 'radio-selection';

const radioElementProps = {
  modelValue: '',
  name: radioBoxName,
  options: [
    {
      id: 'yes',
      label: 'Yes',
    },
    {
      id: 'no',
      label: 'No',
    },
  ],
};

describe('RadioBox Component', () => {
  test('input setting', async () => {
    const wrapper = await mount(RadioBox, {
      propsData: radioElementProps,
    });

    const radioBoxInputYes = await wrapper.find(`[id="${radioElementProps.name}--${radioElementProps.options[0].id}"]`);

    const radioBoxInputNo = await wrapper.find(`[id="${radioElementProps.name}--${radioElementProps.options[1].id}"]`);

    // Expect after mounting that none of both radio options is checked
    expect(radioBoxInputYes.element.checked).toBeFalsy();
    expect(radioBoxInputNo.element.checked).toBeFalsy();
    expect(wrapper.vm.modelValue).toBe('');

    await radioBoxInputYes.trigger('click');

    expect(radioBoxInputYes.element.checked).toBeTruthy();
    expect(radioBoxInputNo.element.checked).toBeFalsy();
    expect(wrapper.vm.modelValue).toBe(radioElementProps.options[0].id);

    wrapper.unmount();
  });

  test('click on label should set modelValue', async () => {
    const wrapper = await mount(RadioBox, {
      propsData: radioElementProps,
    });

    const radioBoxLabelYes = await wrapper.find(`[for="${radioElementProps.name}--${radioElementProps.options[0].id}"]`);
    const radioBoxInputYes = await wrapper.find(`[id="${radioElementProps.name}--${radioElementProps.options[0].id}"]`);

    expect(radioBoxInputYes.element.checked).toBeFalsy();

    await radioBoxLabelYes.trigger('click');

    expect(radioBoxInputYes.element.checked).toBeTruthy();
  });

  test('Check Focus', async () => {
    // to check focus, we need to attach to an actual document, normally we don't do this
    const div = document.createElement('div');
    div.id = 'root';
    document.body.appendChild(div);

    const wrapper = await mount(RadioBox, {
      propsData: radioElementProps,
      attachTo: '#root',
    });
    const radioBoxInputYes = await wrapper.find(`[id="${radioElementProps.name}--${radioElementProps.options[0].id}"]`);

    expect(radioBoxInputYes.element).not.toBe(document.activeElement);

    await radioBoxInputYes.setChecked();

    // TODO Fix test for focus. For some reason it is not working
    // expect(radioBoxInputYes.element).toBe(document.activeElement);
  });
});
