export function registrationErrors(email: string, login: string, password: string) {
  const errors: Record<string, string> = {}
  if (!/^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)+$/.test(email)) {
    errors.email = 'Enter a valid email address.'
  }
  if (!/^[A-Za-z0-9!@#$%^&*_]{3,}$/.test(login)) {
    errors.login = 'Use at least 3 characters: Latin letters, digits, or !@#$%^&*_.'
  }
  if (!/^[A-Za-z0-9!@#$%^&*_]{8,}$/.test(password) || !/[0-9!@#$%^&*_]/.test(password)) {
    errors.password = 'Use at least 8 characters: Latin letters and at least one digit or !@#$%^&*_.'
  }
  return errors
}
