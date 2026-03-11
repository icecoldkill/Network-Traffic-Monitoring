import { type NextRequest, NextResponse } from "next/server"

const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:5000"

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams
  const endpoint = searchParams.get("endpoint")

  if (!endpoint) {
    return NextResponse.json({ error: "Missing endpoint parameter" }, { status: 400 })
  }

  try {
    console.log("[v0] Proxy GET request:", `${BACKEND_URL}${endpoint}`)

    const response = await fetch(`${BACKEND_URL}${endpoint}`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    })

    console.log("[v0] Backend response status:", response.status)
    const text = await response.text()

    if (!response.ok) {
      console.error("[v0] Backend error:", response.status, text.slice(0, 200))
      return NextResponse.json({
        status: "offline",
        message: `Backend returned ${response.status}. Running with mock data.`,
      })
    }

    try {
      const data = JSON.parse(text)
      return NextResponse.json(data)
    } catch {
      console.error("[v0] Non-JSON response from backend")
      return NextResponse.json({ raw: text })
    }
  } catch (error) {
    console.error("[v0] Proxy GET error:", String(error))
    return NextResponse.json({
      status: "offline",
      message: `Cannot reach backend at ${BACKEND_URL}. Make sure Flask is running on port 5000.`,
      error: String(error),
    })
  }
}

export async function POST(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams
  const endpoint = searchParams.get("endpoint")

  if (!endpoint) {
    return NextResponse.json({ error: "Missing endpoint parameter" }, { status: 400 })
  }

  try {
    const body = await request.json()
    console.log("[v0] Proxy POST request:", `${BACKEND_URL}${endpoint}`, body)

    const response = await fetch(`${BACKEND_URL}${endpoint}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    })

    console.log("[v0] Backend response status:", response.status)
    const text = await response.text()

    if (!response.ok) {
      console.error("[v0] Backend error:", response.status, text.slice(0, 200))
      return NextResponse.json({
        status: "offline",
        message: `Backend returned ${response.status}. Running with mock data.`,
      })
    }

    try {
      const data = JSON.parse(text)
      return NextResponse.json(data)
    } catch {
      console.error("[v0] Non-JSON response from backend")
      return NextResponse.json({ raw: text })
    }
  } catch (error) {
    console.error("[v0] Proxy POST error:", String(error))
    return NextResponse.json({
      status: "offline",
      message: `Cannot reach backend at ${BACKEND_URL}. Make sure Flask is running on port 5000.`,
      error: String(error),
    })
  }
}
