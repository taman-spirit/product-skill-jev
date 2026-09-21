# TypeSafe Jev API Reference

Verified against `typesafe-sdk` 0.7.1 (Python), `@typesafe-ai/sdk` 0.6.0 (TypeScript),
and https://docs.typesafe.ai. Check the live docs before relying on a version-specific detail.

## HTTP API

```
POST https://api.typesafe.ai/v1/systemone
Authorization: Bearer <TYPESAFE_API_KEY>
Content-Type: application/json
```

There is also `GET /v1/models` to list models available to the account.

### Request

| Field | Type | Notes |
|-------|------|-------|
| `model` | string | `jev-latest` |
| `state` | string, object, or array | The content to judge. Text only. |
| `questions` | object | Map of your question ID to a question object |

`state` accepts three shapes:

```json
"My card was charged twice."
```
```json
{ "message": "My card was charged twice.", "order_id": "A-104" }
```
```json
["Hi", "My customer number is TS1337.", "My card was charged twice."]
```

Images, audio, and video are not supported. English is the primary training language.
Other languages including Vietnamese and CJK are accepted at lower accuracy, so for Vietnamese
content prefer English instructions and criteria with the Vietnamese text in `state`.

### Question objects

```json
{
  "type": "noul",
  "instructions": "The message requests a refund.",
  "criteria": { "true": "Money back is asked for.", "false": "No refund is asked for." }
}
```
`criteria` is optional for Noul.

```json
{
  "type": "choice",
  "instructions": "What is the main request?",
  "criteria": {
    "refund": "The customer wants money returned.",
    "rebooking": "The customer wants a replacement flight.",
    "information": "The customer is only asking a question.",
    "none": "None of the above apply."
  }
}
```
`criteria` is required for Choice. Up to 255 options. A value of `null` leaves a label
undescribed, which is acceptable only when the label name is self-explanatory.

```json
{
  "type": "score",
  "instructions": "How urgent is this?",
  "criteria": [
    "Can wait until next sprint.",
    "Needs attention this week.",
    "Needs attention today."
  ]
}
```
`criteria` is a required ordered array, 2 to 10 levels, indexed from 0.

`instructions` and each criteria value may be a string, a JSON object, or an array. Use the
structured form when definitions, contrasts, or exclusions make the meaning clearer.

### Response

```json
{
  "model": "jev-1.13",
  "answers": {
    "is_urgent": { "type": "noul", "noul": 0.999 },
    "category":  { "type": "choice", "choice": "billing",
                   "confidence": 0.9,
                   "probabilities": { "billing": 0.8, "technical": 0.1, "other": 0.1 } },
    "urgency":   { "type": "score", "score": 1.7, "confidence": 0.9,
                   "legend": { "0": "Can wait", "1": "This week", "2": "Today" },
                   "probabilities": { "0": 0.1, "1": 0.1, "2": 0.8 } }
  },
  "usage": { "input_tokens": 120, "output_tokens": 12 }
}
```

Field meanings:

- `noul`: probability of yes, from 0 to 1. No confidence field.
- `choice`: the label with the highest probability. `probabilities` sums to about 1.
- `score`: probability-weighted average of the levels, so it can land between integers.
- `legend`: your criteria mapped back to their level numbers, for rendering the result.
- `confidence`: concentration of the distribution, from 0 to 1. Present on Choice and Score only.

### Errors

| Status | Meaning | Retry |
|--------|---------|-------|
| 400 | Bad request | No |
| 401 | Invalid API key | No |
| 403 | Access denied | No |
| 404 | Not found | No |
| 422 | Validation failure, `loc` names the bad field | No, fix the question |
| 429 | Rate limit | Yes, honour `retry-after` |
| 5xx | Server error or overload | Yes, exponential backoff |

Responses carry `x-typesafe-request-id`. Log it on every failure.

## Python SDK

```
pip install typesafe-sdk
```

```python
from typesafe_sdk import Choice, Noul, Score, TypeSafeClient

state = {
    "ticket_message": "My flight was cancelled. Can I get a refund?",
    "refund_policy": "Cancelled flights are eligible for a full refund.",
}

with TypeSafeClient() as client:            # reads TYPESAFE_API_KEY
    response = client.system_one(
        state=state,
        questions={
            "refund_requested": Noul(
                instructions="Does `ticket_message` request a refund?",
            ),
            "request_type": Choice(
                instructions="What is the main request in `ticket_message`?",
                criteria={
                    "refund": "The customer wants money returned.",
                    "rebooking": "The customer wants a replacement flight.",
                    "information": "The customer is asking for information only.",
                    "none": "None of these apply.",
                },
            ),
            "frustration": Score(
                instructions="How frustrated does the customer appear?",
                criteria=[
                    "Calm and neutral.",
                    "Concerned but civil.",
                    "Very angry or using strong language.",
                ],
            ),
        },
    )

refund = response.nouls["refund_requested"].noul            # float 0 to 1
kind = response.choices["request_type"].choice              # str label
kind_conf = response.choices["request_type"].confidence     # float 0 to 1
heat = response.scores["frustration"].score                 # float, may be 1.7
tokens = response.usage.input_tokens
```

Useful surface:

- `TypeSafeClient(api_key=..., model=..., base_url=..., timeout=...)`. Env vars:
  `TYPESAFE_API_KEY`, `TYPESAFE_BASE_URL`, `TYPESAFE_DEFAULT_MODEL`, `TYPESAFE_LOG_LEVEL`.
  Defaults: `https://api.typesafe.ai`, `jev-latest`, 10 second timeout.
- `AsyncTypeSafeClient` mirrors the sync client with `await`.
- `response.answers` holds everything keyed by question ID.
  `response.nouls`, `response.choices`, `response.scores` are typed views of the same data.
- `client.models.list()` returns available models.
- `RetryPolicy(max_retries=2, backoff_initial=0.5, backoff_max=5.0, backoff_jitter=0.25)`
  is the default, retrying 408, 429, and 5xx, and honouring `retry-after`.
- Errors: `TypeSafeAPIError` (has `.status`, `.request_id`), with subclasses
  `TypeSafeAuthenticationError`, `TypeSafeBadRequestError`, `TypeSafePermissionDeniedError`,
  `TypeSafeNotFoundError`, `TypeSafeUnprocessableEntityError`, `TypeSafeRateLimitError`,
  `TypeSafeInternalServerError`, plus `TypeSafeAPIConnectionError` and `TypeSafeAPITimeoutError`.
  All derive from `TypeSafeError`.
- Pass `response_model=` a Pydantic model to get a custom typed response.
- Pass `extra_body=` to use new API fields before the SDK models them.

Error handling pattern for this repo:

```python
from typesafe_sdk import TypeSafeError

try:
    response = client.system_one(state=state, questions=QUESTIONS)
except TypeSafeError as exc:
    logger.warning("Jev unavailable, falling back to manual flow: %s", exc)
    return None          # caller runs the existing interview
```

## TypeScript SDK

```
npm install @typesafe-ai/sdk        # Node 20 or newer
```

```ts
import { choice, noul, score, TypeSafeClient } from "@typesafe-ai/sdk";

const client = new TypeSafeClient();          // reads TYPESAFE_API_KEY

const response = await client.systemOne({
  state: { document: "I was charged twice. Please fix this ASAP." },
  questions: {
    category: choice("What is this ticket about?", {
      billing: "Payments, invoices, or charges.",
      technical: "The product is broken or erroring.",
      other: "Neither of the above.",
    }),
    urgent: noul("Does this need attention today?"),
    severity: score("How severe is the impact?", [
      "Cosmetic or minor.",
      "Workflow is degraded.",
      "Work is blocked.",
    ]),
  },
});

response.answers.category.choice;        // typed as "billing" | "technical" | "other"
response.answers.category.confidence;
response.answers.urgent.noul;
response.answers.severity.score;
```

Helper signatures:

- `noul(instructions?, criteria?)`
- `choice(instructions, criteria)` where criteria is a label to description map
- `score(instructions, criteria)` where criteria is an ordered array

`TypeSafeClientConfig`: `apiKey`, `baseURL`, `defaultModel`, `logLevel`.
Falls back to `TYPESAFE_API_KEY`, `TYPESAFE_BASE_URL`, `TYPESAFE_DEFAULT_MODEL`,
`TYPESAFE_LOG_LEVEL`, then `https://api.typesafe.ai` and `jev-latest`.

Errors: `TypeSafeError` base, then `APIError` with `BadRequestError`, `AuthenticationError`,
`PermissionDeniedError`, `NotFoundError`, `UnprocessableEntityError`, `RateLimitError`,
`InternalServerError`, plus `APIConnectionError`, `APITimeoutError`, `APIUserAbortError`.

Choice labels are inferred as a literal union, so a typo in a branch is a compile error.
Keep question objects in a shared module to get that benefit across the app.

## Further reading

- Docs index: https://docs.typesafe.ai/llms.txt
- Primitives: https://docs.typesafe.ai/primitives.md
- Confidence: https://docs.typesafe.ai/confidence.md
- Patterns: https://docs.typesafe.ai/patterns.md
- Cookbooks worth reading for this repo: hierarchical classification, composite scoring,
  confidence-gated routing, LLM guardrails, and classification using confidence.
