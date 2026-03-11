import { NextResponse } from 'next/server';

export const runtime = 'nodejs';

export async function POST(req: Request) {
  const { messages } = await req.json();
  
  try {
    // Forward the request to the Flask backend
    const response = await fetch('http://localhost:5005/api/chat/stream', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ messages }),
    });

    if (!response.ok) {
      throw new Error(`Backend returned ${response.status}`);
    }

    // Create a streaming response
    const { readable, writable } = new TransformStream();
    const writer = writable.getWriter();
    const encoder = new TextEncoder();

    // Forward the stream from Flask to the client
    if (response.body) {
      const reader = response.body.getReader();
      
      // Process the stream
      const processStream = async () => {
        try {
          while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            
            // Forward the chunk to the client
            await writer.write(value);
          }
        } catch (error) {
          console.error('Stream error:', error);
          await writer.write(encoder.encode('data: ' + JSON.stringify({
            status: 'error',
            message: 'Error processing stream'
          }) + '\n\n'));
        } finally {
          await writer.close();
        }
      };

      // Don't await this to allow streaming
      processStream();
    }

    return new NextResponse(readable, {
      headers: {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
      },
    });
  } catch (error) {
    console.error('Chat API error:', error);
    return NextResponse.json(
      { error: 'Failed to process chat request' },
      { status: 500 }
    );
  }
}

export const dynamic = 'force-dynamic';
