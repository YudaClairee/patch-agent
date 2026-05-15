import { useEffect, useRef, useState } from "react";
import {
  type AgentRunStatus,
  type AgentRunWebSocketFrame,
  createAgentRunWebSocket,
  type TerminalWebSocketFrame,
} from "./api";

type StreamConnectionStatus = "idle" | "connecting" | "connected" | "reconnecting" | "closed";

type UseAgentRunStreamOptions = {
  onTerminal?: (frame: TerminalWebSocketFrame) => void;
};

export type UseAgentRunStreamResult = {
  events: AgentRunWebSocketFrame[];
  status: AgentRunStatus | null;
  prUrl: string | null;
  error: string | null;
  connectionStatus: StreamConnectionStatus;
};

function isTerminalFrame(frame: unknown): frame is TerminalWebSocketFrame {
  return (
    typeof frame === "object" && frame !== null && "type" in frame && (frame as { type: unknown }).type === "terminal"
  );
}

function isAgentRunFrame(frame: unknown): frame is AgentRunWebSocketFrame {
  return (
    typeof frame === "object" &&
    frame !== null &&
    "type" in frame &&
    "payload" in frame &&
    "sequence" in frame &&
    typeof (frame as { sequence: unknown }).sequence === "number"
  );
}

function statusFromFrame(frame: AgentRunWebSocketFrame): AgentRunStatus | null {
  if (frame.type !== "status_change") {
    return null;
  }

  const nextStatus = frame.payload.new_status;

  return isAgentRunStatus(nextStatus) ? nextStatus : null;
}

function isAgentRunStatus(value: unknown): value is AgentRunStatus {
  return (
    value === "queued" || value === "running" || value === "succeeded" || value === "failed" || value === "cancelled"
  );
}

function upsertFrame(events: AgentRunWebSocketFrame[], frame: AgentRunWebSocketFrame) {
  const nextEvents = events.filter((event) => event.sequence !== frame.sequence);
  nextEvents.push(frame);

  return nextEvents.sort((left, right) => left.sequence - right.sequence);
}

export function useAgentRunStream(
  id: string | undefined,
  options: UseAgentRunStreamOptions = {},
): UseAgentRunStreamResult {
  const onTerminalRef = useRef(options.onTerminal);
  const [events, setEvents] = useState<AgentRunWebSocketFrame[]>([]);
  const [status, setStatus] = useState<AgentRunStatus | null>(null);
  const [prUrl, setPrUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<StreamConnectionStatus>("idle");

  useEffect(() => {
    onTerminalRef.current = options.onTerminal;
  }, [options.onTerminal]);

  useEffect(() => {
    setEvents([]);
    setStatus(null);
    setPrUrl(null);
    setError(null);

    if (!id) {
      setConnectionStatus("idle");
      return;
    }

    let socket: WebSocket | null = null;
    let reconnectTimer: number | undefined;
    let reconnectAttempt = 0;
    let closedByHook = false;
    let terminalReceived = false;

    const connect = () => {
      setConnectionStatus(reconnectAttempt === 0 ? "connecting" : "reconnecting");
      socket = createAgentRunWebSocket(id);

      socket.addEventListener("open", () => {
        reconnectAttempt = 0;
        setConnectionStatus("connected");
        setError(null);
      });

      socket.addEventListener("message", (event) => {
        let frame: unknown;

        try {
          frame = JSON.parse(String(event.data));
        } catch {
          setError("Live event stream returned invalid JSON.");
          return;
        }

        if (isTerminalFrame(frame)) {
          terminalReceived = true;
          setStatus(frame.status);
          setPrUrl(frame.pr_url);
          setConnectionStatus("closed");
          onTerminalRef.current?.(frame);
          socket?.close();
          return;
        }

        if (!isAgentRunFrame(frame)) {
          setError("Live event stream returned an unknown frame.");
          return;
        }

        // Negative sequences are synthetic/control frames (e.g. server-side
        // status snapshots, transient runner status labels). Apply their state
        // effects but keep them out of the visible timeline.
        if (frame.sequence >= 0) {
          setEvents((current) => upsertFrame(current, frame));
        }

        const nextStatus = statusFromFrame(frame);
        if (nextStatus) {
          setStatus(nextStatus);
          if (nextStatus === "succeeded" || nextStatus === "failed" || nextStatus === "cancelled") {
            terminalReceived = true;
            setConnectionStatus("closed");
            socket?.close();
            return;
          }
        }

        if (frame.type === "error") {
          const message = frame.payload.message;
          setError(typeof message === "string" ? message : "Agent run reported an error.");
        }
      });

      socket.addEventListener("error", () => {
        setError("Live connection failed. Reconnecting when possible.");
      });

      socket.addEventListener("close", (event) => {
        if (closedByHook || terminalReceived) {
          setConnectionStatus("closed");
          return;
        }

        // Server-side refusals: 1000 normal close, 4001 unauthorized,
        // 4004 run not found, 4005 backend misconfig. None are worth retrying.
        if (event.code === 1000 || (event.code >= 4000 && event.code < 5000)) {
          if (event.code === 4001) {
            setError("Your session expired. Please sign in again.");
          } else if (event.code === 4004) {
            setError("Agent run not found.");
          } else if (event.code === 4005) {
            setError("Live event stream is unavailable.");
          }
          setConnectionStatus("closed");
          return;
        }

        const delay = Math.min(30_000, 1000 * 2 ** reconnectAttempt);
        reconnectAttempt += 1;
        setConnectionStatus("reconnecting");
        reconnectTimer = window.setTimeout(connect, delay);
      });
    };

    connect();

    return () => {
      closedByHook = true;
      if (reconnectTimer) {
        window.clearTimeout(reconnectTimer);
      }
      socket?.close();
    };
  }, [id]);

  return { events, status, prUrl, error, connectionStatus };
}
