import { BASE_URL } from "@/globals";

interface User {
  id: string;
  username: string;
}

interface LoginRequest {
  username: string;
  password: string;
}

interface RegisterRequest {
  username: string;
  password: string;
}

interface LoginResponse {
  userId: string;
  username: string;
  token: string;
  message: string;
}

interface RegisterResponse {
  message: string
  userId: string
  username: string
}

async function login(credentials: LoginRequest): Promise<User> {
  const response = await fetch(BASE_URL + '/login', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(credentials),
    credentials: 'include', // Include cookies in the request
  });

  if (!response.ok) {
    throw new Error('Invalid credentials');
  }

  const data: LoginResponse = await response.json();

  // Store the JWT token from response
  if (data.token) {
    localStorage.setItem('token', data.token);
  }

  // Store user data
  const user = {
    id: data.userId,
    username: data.username || credentials.username
  };
  localStorage.setItem('user', JSON.stringify(user));

  return user;
}

async function register(credentials: RegisterRequest): Promise<User> {
  const response = await fetch(BASE_URL + '/users', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(credentials),
    credentials: 'include',
  })

  if (!response.ok) throw new Error('Failed to create account')

  const data: RegisterResponse = await response.json()

  if (response.status !== 201) throw new Error(data.message || 'Failed to create account')

  // After successful registration, login to get the JWT token
  return login(credentials)
}

function logout(): void {
  localStorage.removeItem('user');
  localStorage.removeItem('token');
}

function getCurrentUser(): User | null {
  const savedUser = localStorage.getItem('user');
  return savedUser ? JSON.parse(savedUser) : null;
}

function getToken(): string | null {
  return localStorage.getItem('token');
}

export {
  login,
  register,
  logout,
  getCurrentUser,
  getToken
};

export type { User, LoginRequest, RegisterRequest, LoginResponse, RegisterResponse };
