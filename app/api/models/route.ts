import { type NextRequest, NextResponse } from "next/server"

export async function POST(request: NextRequest) {
  const formData = await request.formData()
  const model = formData.get("model") as File
  const threshold = formData.get("threshold") as string

  if (!model) {
    return NextResponse.json({ error: "No model file provided" }, { status: 400 })
  }

  try {
    const modelFormData = new FormData()
    modelFormData.append("model", model)
    modelFormData.append("threshold", threshold || "0.75")

    const response = await fetch("http://localhost:5000/api/upload_model", {
      method: "POST",
      body: modelFormData,
    })

    if (!response.ok) {
      throw new Error(`Backend responded with ${response.status}`)
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error("[v0] Model upload error:", error)
    return NextResponse.json({ error: "Failed to upload model" }, { status: 500 })
  }
}
