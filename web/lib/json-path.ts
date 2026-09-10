export function getAtPath(value: unknown, path: string): unknown {
  if (!path.trim()) {
    return value;
  }

  let current: unknown = value;

  for (const segment of path.split(".").filter(Boolean)) {
    if (Array.isArray(current)) {
      const index = Number(segment);
      if (!Number.isInteger(index)) return undefined;
      current = current[index];
      continue;
    }

    if (!current || typeof current !== "object") {
      return undefined;
    }

    current = (current as Record<string, unknown>)[segment];
  }

  return current;
}

export function getStringAtPath(value: unknown, path: string): string | null {
  const found = getAtPath(value, path);
  return typeof found === "string" ? found : null;
}

export function getStringArrayAtPath(value: unknown, path: string): string[] {
  if (!path.trim()) return [];

  const found = getAtPath(value, path);
  if (!Array.isArray(found)) return [];

  return found.filter((item): item is string => typeof item === "string");
}

export function setAtPath(path: string, value: unknown): Record<string, unknown> {
  const segments = path.split(".").map((segment) => segment.trim()).filter(Boolean);
  if (!segments.length) {
    throw new Error("Question path cannot be empty.");
  }

  const root: Record<string, unknown> = {};
  let current = root;

  segments.forEach((segment, index) => {
    if (index === segments.length - 1) {
      current[segment] = value;
      return;
    }

    const child: Record<string, unknown> = {};
    current[segment] = child;
    current = child;
  });

  return root;
}
