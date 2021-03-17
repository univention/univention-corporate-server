import { User } from '@/store/models';

function login(user: User): void {
  if (user.mayLoginViaSAML) {
    window.location.href = `/univention/saml/?location=${window.location.pathname}`;
  } else {
    window.location.href = `/univention/login/?location=${window.location.pathname}`;
  }
}

function logout(): void {
  window.location.href = '/univention/logout';
}

export { login, logout };
