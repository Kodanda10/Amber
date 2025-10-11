import { NextResponse } from 'next/server';
import { backendClient } from '@/lib/backendClient';

export async function GET() {
  const { leaders, posts, source } = await backendClient.getDashboard();
  return NextResponse.json({ leaders, posts, source });
}
