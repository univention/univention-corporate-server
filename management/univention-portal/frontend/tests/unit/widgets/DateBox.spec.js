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

import DateBox from '@/components/widgets/DateBox.vue';

describe('DateBox Component', () => {
  test('date input is working as expected', async () => {
    const wrapper = await mount(DateBox, {
      propsData: {
        modelValue: '',
        name: 'datebox',
        forAttrOfLabel: '',
        invalidMessageId: '',
      },
    });

    const dateBox = await wrapper.find('[data-test="date-box"]');

    // Expect input value to be empty on mount.
    expect(dateBox.element.value).toBe('');
    await dateBox.setValue('2017-06-01');
    expect(dateBox.element.value).toBe('2017-06-01');

    // TODO check if wrong date input return false eg: 30.02.1993

    await dateBox.setValue('text string');
    expect(dateBox.element.value).not.toBe('text string');
    expect(dateBox.element.value).toBe('');

    wrapper.unmount();
  });

  test('this.invalid should return correct boolean', async () => {
    const wrapper = await mount(DateBox, {
      propsData: {
        modelValue: '',
        name: 'datebox',
        forAttrOfLabel: '',
        invalidMessageId: '',
      },
    });

    // this.invalid returns true if this.invalidMessage has a non-empty string
    expect(wrapper.vm.invalid).toBe(false);
    await wrapper.setProps({ invalidMessage: 'Invalid Message' });
    expect(wrapper.vm.invalid).toBe(true);

    // TODO select element should have aria-invalid true or false
    // depending on this.invalid
  });

  test('it is an input type=date', async () => {
    const wrapper = await mount(DateBox, {
      propsData: {
        modelValue: '',
        name: 'datebox',
        forAttrOfLabel: '',
        invalidMessageId: '',
      },
    });
    const dateBox = await wrapper.find('[data-test="date-box"]');
    expect(dateBox.attributes('type')).toBe('date');
  });

  test('it has the attribute id with a value from Prop //A11y', async () => {
    const wrapper = await mount(DateBox, {
      propsData: {
        modelValue: '',
        forAttrOfLabel: 'testString',
        name: 'datebox',
        invalidMessageId: '',
      },
    });
    const dateBox = await wrapper.find('[data-test="date-box"]');
    expect(dateBox.attributes('id')).toBe('testString');
  });
});
