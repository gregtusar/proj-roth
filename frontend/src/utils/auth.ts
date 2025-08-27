export function isTokenExpired(token: string): boolean {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    const exp = payload.exp;
    
    if (!exp) {
      return true;
    }
    
    // Check if token expires in the next 5 minutes (to refresh early)
    const expirationTime = exp * 1000;
    const currentTime = Date.now();
    const bufferTime = 5 * 60 * 1000; // 5 minutes
    
    return currentTime >= expirationTime - bufferTime;
  } catch (error) {
    console.error('Error checking token expiration:', error);
    return true;
  }
}

export function getTokenExpiration(token: string): Date | null {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    const exp = payload.exp;
    
    if (!exp) {
      return null;
    }
    
    return new Date(exp * 1000);
  } catch (error) {
    console.error('Error getting token expiration:', error);
    return null;
  }
}