import { NextResponse } from "next/server";

export function GET() {
  return NextResponse.json({
    status: "ok",
    product: "tracerag",
    version: "0.3.0-alpha",
  });
}
