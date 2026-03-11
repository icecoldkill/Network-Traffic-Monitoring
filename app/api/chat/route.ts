import { type NextRequest, NextResponse } from "next/server"

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const backendUrl = process.env.BACKEND_URL || "http://127.0.0.1:5000"

    console.log("[v0] Chat request forwarded to:", `${backendUrl}/api/chat`)

    const response = await fetch(`${backendUrl}/api/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    })

    const data = await response.json()

    if (!response.ok) {
      return NextResponse.json({
        status: "error",
        message: `Backend error: ${data.message || "Unknown error"}`,
      })
    }

    return NextResponse.json(data)
  } catch (error) {
    console.error("[v0] Chat endpoint error:", error)
    return NextResponse.json({
      status: "offline",
      message: `Cannot reach backend. Make sure Flask is running on port 5000.`,
      error: String(error),
    })
  }
}
