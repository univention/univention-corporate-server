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

beforeEach(() => {
  cy.clearCookie('univentionCookieSettingsAccepted');
  cy.setCookie('UMCLang', 'de_DE');
  // stuff selenium can't do #1: mock requests / responses
  cy.intercept('GET', 'portal.json', { fixture: 'portal_logged_out.json' });
  // cy.intercept('GET', 'portal/portal.json', { fixture: 'portal_logged_in.json' });
  cy.intercept('GET', 'meta.json', { fixture: 'meta.json' });
  cy.intercept('GET', 'de.json', { fixture: 'de.json' });
  cy.intercept('GET', 'languages.json', { fixture: 'languages.json' });
  cy.visit('/');
  cy.get('main.cookie-banner + footer button.primary').click();
});

describe('Test Portal Landing', () => {
  it('General loading of tiles and menu', () => {
    cy.contains('h2', 'Verwaltung');
    // Tiles?
    cy.get('.portal-tile__name').contains('span', 'Univention Blog');

    cy.get('[data-test="navigationbutton"]').click();
    cy.wait(500);
    cy.get('.portal-sidenavigation__link').contains('Anmelden');
    cy.contains('Zertifikate');
    cy.contains('Apps');
    cy.contains('Hilfe');
  });

  it('Mouseover is working', () => {
    // Mouseover tooltip?
    cy.get('.portal-category .portal-tile').first().trigger('mouseenter');
    cy.get('[data-test="portal-tooltip"]').contains('ownCloud');
    cy.get('.portal-category .portal-tile').first().trigger('mouseleave');
    cy.get('[data-test="portal-tooltip"]').should('not.exist');
  });
  it('Headerbuttons become green', () => {
    // Buttons, check if they become green
    const searchbutton = cy.get('[data-test="searchbutton"]');
    searchbutton.should('not.have.class', 'header-button--is-active');
    searchbutton.click();
    searchbutton.should('have.class', 'header-button--is-active');

    const bellbutton = cy.get('[data-test="bellbutton"]');
    bellbutton.should('not.have.class', 'header-button--is-active');
    bellbutton.click();
    bellbutton.should('have.class', 'header-button--is-active');

    const menubutton = cy.get('[data-test="navigationbutton"]');
    menubutton.should('not.have.class', 'header-button--is-active');
    menubutton.click();
    menubutton.should('have.class', 'header-button--is-active');
    cy.get('.modal-wrapper--isVisible').click();
  });
  it('Cookie should exist', () => {
    cy.getCookie('univentionCookieSettingsAccepted').should('exist');
  });
  it('General a11y test', () => {
    cy.injectAxe();
    cy.checkA11y('body', 
    {
      runOnly: {
        type: 'tag',
        values: ['wcag21aa'],
      }
    },
    cy.terminalLog, {
      skipFailures: true
    });
  });
});
