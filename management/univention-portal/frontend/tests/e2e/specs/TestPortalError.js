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

import 'cypress-axe';

const loadOtherFiles = () => {
  cy.intercept('GET', 'meta.json', { fixture: 'meta.json' });
  cy.intercept('GET', 'de.json', { fixture: 'de.json' });
  cy.intercept('GET', 'languages.json', { fixture: 'languages.json' });
  cy.setCookie('univentionCookieSettingsAccepted', 'doesthisneedavalue');
};

describe('Test Portal Error Components', () => {
  it('Shows Error if portal.json is not returned successfully', () => {
    cy.intercept('GET', 'portal.json', { statusCode: 500 });
    loadOtherFiles();
    cy.visit('/');

    const errorContainer = cy.get('.portal-error');

    errorContainer.should('be.visible');
    errorContainer.should((container) => {
      // make sure the first contains text "sorry"
      expect(container.first()).to.contain('Sorry');
    });
  });

  it('Shows Not found component if given url is false', () => {
    cy.intercept('GET', 'portal.json', { fixture: 'portal_logged_in.json' });
    loadOtherFiles();

    // invalid url after "#"
    cy.visit('/#/gibberish');

    const errorContainer = cy.get('.portal-error');
    errorContainer.should('be.visible');
    errorContainer.should((container) => {
      // make sure the first contains text "sorry"
      expect(container.first()).to.contain('Page not found');
    });
  });

  it('General a11y test', () => {
    cy.injectAxe();
    cy.checkA11y('body',
      {
        runOnly: {
          type: 'tag',
          values: ['wcag21aa'],
        },
      },
      cy.terminalLog, {
        skipFailures: true,
      });
  });
});
