# P10 n8n Workflow - REAL HTTP 429 Demo Ready

## What changed

This revision fixes the classroom issue where the JSON body showed `backendStatusCode: 429`, but Postman still displayed `200 OK`.

The root cause was the n8n **Respond Error** node returning HTTP `200`, even though the backend API returned `429`. In HTTP terms, n8n was saying: "the workflow handled the request successfully," not: "the backend accepted the request." For teaching API reliability, this can confuse students.

## Revised behavior

- Success branch:
  - `backendStatusCode`: `200`
  - Postman HTTP status: `200 OK`
  - `workflowBranch`: `TRUE_BRANCH_SUCCESS`
  - `executedNode`: `Build Success Response`

- Error/rate-limit branch:
  - `backendStatusCode`: `429`
  - Postman HTTP status: `429 Too Many Requests`
  - `workflowBranch`: `FALSE_BRANCH_ERROR`
  - `executedNode`: `Build Error Response`

## Files to import

1. n8n workflow:
   - `P10_API_Reliability_Workflow_REAL_HTTP_429_Demo_Ready.json`

2. Postman collection:
   - `Postman_Collection_P10_P16_REAL_HTTP_429.postman_collection.json`

3. Postman environment:
   - `Postman_Environment_CommProto_Local_REAL_HTTP_429.postman_environment.json`

## Demo steps

1. Start `server.py` on `http://localhost:8088`.
2. Start n8n on `http://localhost:5678`.
3. Import the revised n8n workflow.
4. Publish the workflow.
5. Import the revised Postman collection and environment.
6. Run `P10 Reset Reliability State` once.
7. Run `P10 n8n Webhook Trigger` with Postman Runner:
   - Iterations: `8`
   - Delay: `0 ms`

## Expected result

- Iteration 1-3: `200 OK`, success branch.
- Iteration 4+: `429 Too Many Requests`, error branch.

The Postman test script now validates this explicitly:

```javascript
pm.expect(pm.response.code).to.eql(jsonData.backendStatusCode);
```

This makes the demo more realistic: the API response body and the HTTP status code are aligned.
