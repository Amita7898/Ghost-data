import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { mergeEvents, parseSource, type Event } from "./api";
import { Badge, EventCard, ResultPanel, Modal } from "./components";
afterEach(cleanup);
it("deduplicates reconnect events without losing their ordering", () => {
  const e = (seq: number) => ({
    seq,
    elapsed_seconds: seq,
    kind: "tool_requested",
    data: {},
  });
  expect(mergeEvents([e(1), e(2)], [e(2), e(3)]).map((x) => x.seq)).toEqual([
    1, 2, 3,
  ]);
});
it("accepts only registered locator syntax", () => {
  expect(parseSource("javascript:alert(1)")).toBeNull();
  expect(
    parseSource("sha256:" + "a".repeat(64) + "#/observations/2")?.pointer,
  ).toBe("/observations/2");
});
it("keeps replay distinct from live inference", () => {
  render(<Badge value="replay" mode />);
  expect(screen.getByText("replay")).toHaveClass("amber");
});
it("renders source injection as text and rejected hypotheses as rejected", () => {
  const event: Event = {
    seq: 1,
    elapsed_seconds: 2,
    kind: "hypothesis_validated",
    data: {
      name: "submit_hypothesis",
      result: {
        accepted: false,
        reason: "Unsupported source",
        proposal: {
          claim: "STATE",
          value: "ABSENT",
          quote: "<img src=x onerror=alert(1)>",
        },
      },
    },
  };
  const { container } = render(<EventCard event={event} onSource={() => {}} />);
  expect(screen.getByText("rejected")).toBeInTheDocument();
  expect(container.querySelector("img")).toBeNull();
  expect(screen.getByText("<img src=x onerror=alert(1)>")).toBeInTheDocument();
});
it("separates model summary from audit authority", () => {
  render(
    <EventCard
      event={{
        seq: 1,
        elapsed_seconds: 1,
        kind: "model_summary",
        data: { summary: "Untrusted interpretation" },
      }}
      onSource={() => {}}
    />,
  );
  expect(screen.getByText(/NOT THE AUDIT AUTHORITY/)).toBeInTheDocument();
});
it("shows original event details instead of fabricated thoughts", () => {
  render(
    <EventCard
      event={{
        seq: 3,
        elapsed_seconds: 10,
        kind: "tool_requested",
        data: { name: "read_evidence", arguments: { evidence_id: "source-a" } },
      }}
      onSource={() => {}}
    />,
  );
  fireEvent.click(screen.getByText("Show event details"));
  expect(screen.getByText(/"evidence_id": "source-a"/)).toBeInTheDocument();
});
it("does not invent a conclusion before a report exists", () => {
  render(<ResultPanel run={null} onEvidence={() => {}} />);
  expect(screen.getByText("Evidence before certainty.")).toBeInTheDocument();
  expect(screen.queryByText("verified within scope")).not.toBeInTheDocument();
});

it("source dialog focuses a control, traps reverse tab and restores previous focus", () => {
  const previous = document.createElement("button");
  document.body.append(previous);
  previous.focus();
  const close = vi.fn();
  const view = render(
    <Modal title="Evidence" onClose={close}>
      <button>Last source control</button>
    </Modal>,
  );
  const first = screen.getByRole("button", {
      name: "Close evidence inspector",
    }),
    last = screen.getByRole("button", { name: "Last source control" });
  expect(first).toHaveFocus();
  fireEvent.keyDown(document, { key: "Tab", shiftKey: true });
  expect(last).toHaveFocus();
  fireEvent.keyDown(document, { key: "Tab" });
  expect(first).toHaveFocus();
  fireEvent.keyDown(document, { key: "Escape" });
  expect(close).toHaveBeenCalledOnce();
  view.unmount();
  expect(previous).toHaveFocus();
  previous.remove();
});
