import { NextResponse } from 'next/server';
import { backendClient } from '@/lib/backendClient';

export async function DELETE(_: Request, context: { params: Promise<{ id: string }> }) {
  const { id } = await context.params;
  await backendClient.removeLeader(id);
  return NextResponse.json({ success: true });
}
