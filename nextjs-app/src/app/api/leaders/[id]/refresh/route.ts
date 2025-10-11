import { NextResponse } from 'next/server';
import { backendClient } from '@/lib/backendClient';

export async function POST(_: Request, context: { params: Promise<{ id: string }> }) {
  const { id } = await context.params;
  const { posts } = await backendClient.refreshLeader(id);
  return NextResponse.json({ posts });
}
