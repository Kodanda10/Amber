import { NextResponse } from 'next/server';
import { backendClient } from '@/lib/backendClient';

export async function GET() {
  const { leaders } = await backendClient.getDashboard();
  return NextResponse.json({ leaders });
}

export async function POST(request: Request) {
  const json = await request.json();
  const { leader } = await backendClient.createLeader(json);
  return NextResponse.json(leader, { status: 201 });
}
