import { NextResponse } from "next/server"

const BACKEND_URL = "http://localhost:5000"

export async function GET() {
  try {
    const response = await fetch(`${BACKEND_URL}/`, {
      method: "GET",
    })

    if (response.ok) {
      return NextResponse.json({
        status: "healthy",
        backend: "connected",
        url: BACKEND_URL,
      })
    } else {
      return NextResponse.json(
        {
          status: "unhealthy",
          backend: "error",
          statusCode: response.status,
          message: "Backend returned error",
        },
        { status: 503 },
      )
    }
  } catch (error) {
    return NextResponse.json(
      {
        status: "offline",
        backend: "unreachable",
        message: `Cannot reach Flask backend at ${BACKEND_URL}`,
        error: String(error),
      },
      { status: 503 },
    )
  }
}
