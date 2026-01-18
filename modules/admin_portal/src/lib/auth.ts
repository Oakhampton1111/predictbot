import { NextAuthOptions } from 'next-auth';
import CredentialsProvider from 'next-auth/providers/credentials';
import { prisma } from './prisma';
import { compare, hash } from 'bcryptjs';
import type { Role } from '@/types';

// Extend the built-in session types
declare module 'next-auth' {
  interface Session {
    user: {
      id: string;
      username: string;
      email?: string;
      role: Role;
    };
  }

  interface User {
    id: string;
    username: string;
    email?: string;
    role: Role;
  }
}

declare module 'next-auth/jwt' {
  interface JWT {
    id: string;
    username: string;
    role: Role;
  }
}

export const authOptions: NextAuthOptions = {
  providers: [
    CredentialsProvider({
      name: 'Credentials',
      credentials: {
        username: { label: 'Username', type: 'text' },
        password: { label: 'Password', type: 'password' },
      },
      async authorize(credentials) {
        if (!credentials?.username || !credentials?.password) {
          throw new Error('Username and password are required');
        }

        // Check for environment-based admin user first
        const envUsername = process.env.ADMIN_USERNAME;
        const envPassword = process.env.ADMIN_PASSWORD;

        if (
          envUsername &&
          envPassword &&
          credentials.username === envUsername &&
          credentials.password === envPassword
        ) {
          return {
            id: 'env-admin',
            username: envUsername,
            role: 'ADMIN' as Role,
          };
        }

        // Check database for user
        try {
          const user = await prisma.user.findUnique({
            where: { username: credentials.username },
          });

          if (!user) {
            throw new Error('Invalid username or password');
          }

          const isValidPassword = await compare(credentials.password, user.passwordHash);

          if (!isValidPassword) {
            throw new Error('Invalid username or password');
          }

          // Update last login
          await prisma.user.update({
            where: { id: user.id },
            data: { lastLogin: new Date() },
          });

          return {
            id: user.id,
            username: user.username,
            role: user.role as Role,
          };
        } catch (error) {
          // If database is not available, only allow env-based auth
          console.error('Database auth error:', error);
          throw new Error('Authentication failed');
        }
      },
    }),
  ],
  callbacks: {
    async jwt({ token, user }) {
      if (user) {
        token.id = user.id;
        token.username = user.username;
        token.role = user.role;
      }
      return token;
    },
    async session({ session, token }) {
      session.user = {
        id: token.id,
        username: token.username,
        role: token.role,
      };
      return session;
    },
  },
  pages: {
    signIn: '/login',
    error: '/login',
  },
  session: {
    strategy: 'jwt',
    maxAge: 24 * 60 * 60, // 24 hours
  },
  secret: process.env.NEXTAUTH_SECRET,
};

// Role-based access control helpers
export function canManageStrategies(role: Role): boolean {
  return role === 'ADMIN' || role === 'OPERATOR';
}

export function canManagePositions(role: Role): boolean {
  return role === 'ADMIN' || role === 'OPERATOR';
}

export function canEditConfig(role: Role): boolean {
  return role === 'ADMIN';
}

export function canUseEmergencyControls(role: Role): boolean {
  return role === 'ADMIN' || role === 'OPERATOR';
}

export function canViewAuditLogs(role: Role): boolean {
  return role === 'ADMIN';
}

export function canManageUsers(role: Role): boolean {
  return role === 'ADMIN';
}

// Utility to hash passwords
export async function hashPassword(password: string): Promise<string> {
  return hash(password, 12);
}

// Audit logging helper
export async function logAuditAction(
  userId: string,
  action: string,
  resource: string,
  details?: Record<string, unknown>,
  request?: { ip?: string; userAgent?: string }
) {
  try {
    await prisma.auditLog.create({
      data: {
        userId,
        action,
        resource,
        details: details ? JSON.parse(JSON.stringify(details)) : undefined,
        ipAddress: request?.ip,
        userAgent: request?.userAgent,
      },
    });
  } catch (error) {
    console.error('Failed to create audit log:', error);
  }
}

export default authOptions;
