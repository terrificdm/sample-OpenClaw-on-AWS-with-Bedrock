/**
 * openclaw AgentCore utility functions
 * Handles SessionKey derivation and invocation response formatting.
 */

/**
 * Derives the openclaw SessionKey for a given tenant.
 * Format: agentcore:{tenantId}
 * This value is passed as the `user` field in POST /v1/chat/completions
 * and used by getReplyFromConfig() as the SessionKey.
 *
 * Validates: Requirements 1.3, 2.3
 */
export function deriveSessionKey(tenantId: string): string {
  return `agentcore:${tenantId}`;
}

/**
 * Formats an invocation response to ensure it always contains a `choices` array.
 * AgentCore Runtime expects OpenAI-compatible response format.
 *
 * - If payload already has a `choices` array, return as-is.
 * - Otherwise wrap it: { choices: [{ message: { content: JSON.stringify(payload) } }], ...payload }
 *
 * Validates: Requirements 1.4
 */
export function formatInvocationResponse(payload: unknown): object {
  if (
    payload !== null &&
    typeof payload === "object" &&
    !Array.isArray(payload) &&
    Array.isArray((payload as Record<string, unknown>)["choices"])
  ) {
    return payload as object;
  }

  const content =
    typeof payload === "string" ? payload : JSON.stringify(payload);

  return {
    ...(payload !== null && typeof payload === "object" && !Array.isArray(payload)
      ? (payload as object)
      : {}),
    choices: [
      {
        message: {
          content,
        },
      },
    ],
  };
}
