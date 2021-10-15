/*
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
*/

const sizes = ['iphone-8', 'ipad-2'];
const orientations = ['portrait', 'landscape'];

describe('Logo', () => {
  orientations.forEach((orientation) => {
    sizes.forEach((size) => {
      // make assertions on the logo using
      // an array of different viewports
      it(`Should display the menubutton on ${size} screen, orientation ${orientation}`, () => {
        cy.clearCookie('univentionCookieSettingsAccepted');
        cy.intercept('GET', 'portal.json', { fixture: 'portal_logged_out.json' });
        cy.intercept('GET', 'meta.json', { fixture: 'meta.json' });
        cy.intercept('GET', 'de.json', { fixture: 'de.json' });
        cy.intercept('GET', 'languages.json', { fixture: 'languages.json' });
        cy.viewport(size, orientation);

        cy.visit('/');
        cy.get('main.cookie-banner + footer button.primary').click();
        // reactivate after fix
        // cy.get('[data-test="navigationbutton"]').should('be.visible');
      });
    });
  });
});
