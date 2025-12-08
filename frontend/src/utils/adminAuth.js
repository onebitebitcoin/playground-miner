export const getCurrentUsername = () => {
  return localStorage.getItem('nickname') || 'anonymous'
}

export const getAdminUsername = () => {
  const nickname = localStorage.getItem('nickname')
  const adminStatus = localStorage.getItem('isAdmin')
  return nickname === 'admin' && adminStatus === 'true' ? 'admin' : ''
}
