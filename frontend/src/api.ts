import type { components } from "./api.generated";
export type Investigation = components["schemas"]["Investigation"];
export type Run = components["schemas"]["Run"];
export type Artifact = components["schemas"]["Artifact"];
export type Bundle = components["schemas"]["Bundle"];
export type Event = components["schemas"]["Event"];
export type Context = components["schemas"]["Context"];
export type Demo = components["schemas"]["Demo"];
export type Runtime = components["schemas"]["RuntimeStatus"];
export const base = "/api/v1";
export async function api<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const response = await fetch(base + path, {
    ...options,
    headers: { "Content-Type": "application/json", ...options.headers },
  });
  if (!response.ok) {
    const value = await response
      .json()
      .catch(() => ({ message: "Backend connection failed" }));
    throw new Error(
      [
        value.message,
        ...(value.details || []).map(
          (d: { location: string; message: string }) =>
            `${d.location}: ${d.message}`,
        ),
      ].join(" · "),
    );
  }
  return response.json();
}
export function upload(
  id: string,
  file: File,
  onProgress: (value: number) => void,
): Promise<Artifact> {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open("PUT", base + `/investigations/${id}/evidence`);
    xhr.setRequestHeader("Content-Type", "application/json");
    xhr.setRequestHeader("X-Filename", file.name);
    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable)
        onProgress(Math.round((e.loaded / e.total) * 100));
    };
    xhr.onerror = () => reject(new Error("Upload interrupted. Please retry."));
    xhr.onload = () => {
      let value;
      try {
        value = JSON.parse(xhr.responseText);
      } catch {
        reject(new Error("Invalid server response"));
        return;
      }
      if (xhr.status >= 400)
        reject(
          new Error(
            [
              value.message,
              ...(value.details || []).map(
                (d: { message: string }) => d.message,
              ),
            ].join(" · "),
          ),
        );
      else resolve(value);
    };
    xhr.send(file);
  });
}
export const date = (value: string) =>
  new Date(value).toLocaleString(undefined, {
    month: "short",
    year: "numeric",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    timeZone: "UTC",
    timeZoneName: "short",
  });
export const human = (value: string) =>
  value.toLowerCase().replaceAll("_", " ");
export function mergeEvents(old: Event[], incoming: Event[]) {
  return [
    ...new Map([...old, ...incoming].map((e) => [e.seq, e])).values(),
  ].sort((a, b) => a.seq - b.seq);
}
export function parseSource(source: string) {
  const match =
    /^sha256:([a-f0-9]{64})#(\/(?:observations|identities|targets|rules)\/\d+)$/.exec(
      source,
    );
  return match ? { sha: match[1], pointer: match[2] } : null;
}

export const terminal = (run: Run) =>
  [
    "completed",
    "cancelled",
    "failed",
    "interrupted",
    "verification_failed",
  ].includes(run.status);
