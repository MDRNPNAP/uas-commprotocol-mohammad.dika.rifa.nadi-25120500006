const jsonHeaders = { "Content-Type": "application/json" };
let ws = null;
let wsHeartbeat = null;

const wsTemplates = {
  dashboard_refresh: {
    event: "dashboard_refresh",
    dashboard: "sales-ops",
    value: 1,
    changedMetric: "orders_per_minute"
  },
  order_created: {
    event: "order_created",
    orderId: "ORD-2026-001",
    amount: 450000,
    priority: "normal"
  },
  sensor_alert: {
    event: "sensor_alert",
    deviceId: "sensor-01",
    temperature: 38.4,
    severity: "warning"
  },
  chat_message: {
    event: "chat_message",
    user: "student-01",
    message: "Realtime message from WebSocket lab"
  }
};

const grpcTemplates = {
  Predict: {
    customerId: "C-1024",
    features: {
      avgOrderValue: 250000,
      monthlyOrders: 7
    }
  },
  BatchPredict: {
    items: [
      {
        customerId: "C-1001",
        features: {
          avgOrderValue: 150000,
          monthlyOrders: 3
        }
      },
      {
        customerId: "C-1002",
        features: {
          avgOrderValue: 420000,
          monthlyOrders: 9
        }
      }
    ]
  },
  HealthCheck: {}
};

const restTemplates = {
  products: {
    POST: {
      name: "Smart Sensor",
      category: "iot",
      price: 175000,
      stock: 12
    },
    PUT: {
      name: "Laptop Pro 14 Replacement",
      category: "computer",
      price: 15500000,
      stock: 4
    },
    PATCH: {
      stock: 2,
      price: 14900000
    }
  },
  users: {
    POST: {
      username: "data.student",
      email: "data.student@example.edu",
      role: "student",
      status: "active",
      department: "Sains Data"
    },
    PUT: {
      username: "student.demo.updated",
      email: "student.demo.updated@example.edu",
      role: "student",
      status: "active",
      department: "Sains Data"
    },
    PATCH: {
      status: "inactive"
    }
  },
  profiles: {
    POST: {
      userId: 1,
      fullName: "Student Demo",
      program: "Sains Data",
      semester: 2,
      skills: ["postman", "json", "wireshark"],
      city: "Jakarta"
    },
    PUT: {
      userId: 1,
      fullName: "Student Demo Updated",
      program: "Sains Data",
      semester: 2,
      skills: ["postman", "python", "api testing"],
      city: "Jakarta"
    },
    PATCH: {
      skills: ["postman", "mqtt", "grpc"]
    }
  },
  orders: {
    POST: {
      orderId: "ORD-UTS-003",
      customer: "Student Mart",
      amount: 325000,
      status: "created",
      items: ["api-lab-kit"],
      channel: "postman"
    },
    PUT: {
      orderId: "ORD-2026-001",
      customer: "CakraMart Updated",
      amount: 500000,
      status: "paid",
      items: ["temperature-sensor", "router"],
      channel: "postman-lab"
    },
    PATCH: {
      status: "shipped"
    }
  },
  transactions: {
    POST: {
      transactionId: "TRX-UTS-003",
      orderId: "ORD-UTS-003",
      method: "virtual_account",
      amount: 325000,
      status: "pending",
      paidAt: null,
      channel: "payment-gateway"
    },
    PUT: {
      transactionId: "TRX-2026-001",
      orderId: "ORD-2026-001",
      method: "bank_transfer",
      amount: 450000,
      status: "settled",
      paidAt: "2026-06-01T09:00:00+0700",
      channel: "payment-gateway"
    },
    PATCH: {
      status: "settled"
    }
  }
};

function pretty(value) {
  if (typeof value === "string") return value;
  return JSON.stringify(value, null, 2);
}

function byId(id) {
  return document.getElementById(id);
}

function on(id, event, handler) {
  const element = byId(id);
  if (element) element.addEventListener(event, handler);
}

function setOutput(id, value) {
  const element = byId(id);
  if (element) element.textContent = value;
}

function readJson(id) {
  const raw = byId(id).value;
  try {
    return JSON.parse(raw);
  } catch (error) {
    throw new Error(`Invalid JSON in ${id}: ${error.message}`);
  }
}

async function request(method, path, body) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 10000);
  const options = { method, headers: {} };
  options.signal = controller.signal;
  if (body !== undefined) {
    options.headers = jsonHeaders;
    options.body = typeof body === "string" ? body : JSON.stringify(body);
  }
  try {
    const response = await fetch(path, options);
    const text = await response.text();
    let parsed = text;
    try { parsed = JSON.stringify(JSON.parse(text), null, 2); } catch (_) {}
    return `${method} ${path}\nHTTP ${response.status} ${response.statusText}\n\n${parsed || "(no response body)"}`;
  } finally {
    clearTimeout(timeoutId);
  }
}

async function run(outputId, fn) {
  try {
    setOutput(outputId, "Processing request...");
    setOutput(outputId, await fn());
  } catch (error) {
    setOutput(outputId, `Request failed: ${error.message}`);
  }
}

function setPage(page) {
  document.querySelectorAll(".nav").forEach(btn => btn.classList.toggle("active", btn.dataset.page === page));
  document.querySelectorAll(".page").forEach(section => section.classList.toggle("active", section.id === `page-${page}`));
}

document.querySelectorAll(".nav").forEach(btn => btn.addEventListener("click", () => setPage(btn.dataset.page)));

async function checkHealth() {
  try {
    const response = await fetch("/api/health");
    byId("serverStatus").textContent = response.ok ? "Server OK" : "Server issue";
  } catch (_) {
    byId("serverStatus").textContent = "Server offline";
  }
}

async function loadProducts() {
  const resource = byId("restResource")?.value || "products";
  const response = await fetch(`/api/${resource}`);
  const payload = await response.json();
  setOutput("resourceSnapshot", pretty(payload));
}

function setRestDefaults() {
  const method = byId("restMethod").value;
  const resource = byId("restResource")?.value || "products";
  const path = byId("restPath");
  path.value = ["PUT", "PATCH", "DELETE"].includes(method) ? `/api/${resource}/1` : `/api/${resource}`;
  const template = restTemplates[resource]?.[method] || restTemplates[resource]?.POST || {};
  byId("restBody").value = pretty(template);
}

on("restMethod", "change", () => setRestDefaults());

on("restResource", "change", async () => {
  setRestDefaults();
  await loadProducts();
});

async function restQuickDemo(resource, method, outputId) {
  const template = restTemplates[resource] || restTemplates.products;
  const collectionPath = `/api/${resource}`;
  const itemPath = `/api/${resource}/1`;
  byId("restResource").value = resource;
  byId("restMethod").value = method;
  setRestDefaults();
  if (method === "GET") {
    return request("GET", collectionPath);
  }
  if (method === "POST") {
    return request("POST", collectionPath, template.POST);
  }
  if (method === "PUT") {
    return request("PUT", itemPath, template.PUT);
  }
  if (method === "PATCH") {
    return request("PATCH", itemPath, template.PATCH);
  }
  if (method === "DELETE") {
    const createText = await request("POST", collectionPath, template.POST);
    const match = createText.match(/"id":\s*(\d+)/);
    const deletePath = match ? `/api/${resource}/${match[1]}` : `/api/${resource}/2`;
    const deleteText = await request("DELETE", deletePath);
    return `${createText}\n\n--- DELETE created temporary item ---\n\n${deleteText}`;
  }
  return `Unsupported method ${method}`;
}

document.querySelectorAll("[data-rest-resource][data-rest-method]").forEach(btn => {
  btn.addEventListener("click", async () => {
    const page = btn.closest(".page").id.replace("page-", "");
    const outputId = page === "uts" ? "utsOutput" : "restResponse";
    const resource = btn.dataset.restResource;
    const method = btn.dataset.restMethod;
    await run(outputId, async () => {
      const result = await restQuickDemo(resource, method, outputId);
      await loadProducts();
      return result;
    });
  });
});

on("sendRest", "click", async () => {
  const method = byId("restMethod").value;
  const path = byId("restPath").value;
  const body = byId("restBody").value;
  await run("restResponse", async () => {
    const result = await request(method, path, ["GET", "DELETE"].includes(method) ? undefined : body);
    await loadProducts();
    return result;
  });
});

on("resetProducts", "click", async () => {
  await run("restResponse", async () => {
    const result = await request("POST", "/api/reset", {});
    await loadProducts();
    return result;
  });
});

document.querySelectorAll("[data-fetch]").forEach(btn => {
  btn.addEventListener("click", async () => {
    const page = btn.closest(".page").id.replace("page-", "");
    const outputId = `${page}Output`;
    await run(outputId, () => request("GET", btn.dataset.fetch));
  });
});

on("sendWebhook", "click", async () => {
  const body = { source: "postman-demo", event: "order.created", orderId: "ORD-2026-001", amount: 450000 };
  await run("utsOutput", () => request("POST", "/api/webhook/inbox", body));
});

on("submitUtsEvidence", "click", async () => {
  const body = {
    studentId: "NIM-DEMO",
    case: "UTS API + packet capture evidence",
    methods: ["GET", "POST"],
    evidence: ["postman-screenshot", "curl-command", "pcapng-optional"]
  };
  await run("utsOutput", () => request("POST", "/api/uts/evidence", body));
});

on("wsTemplate", "change", event => {
  byId("wsMessage").value = pretty(wsTemplates[event.target.value]);
});

on("connectWs", "click", () => {
  const log = byId("wsLog");
  const channel = encodeURIComponent(byId("wsChannel").value);
  if (ws && ws.readyState === WebSocket.OPEN) ws.close();
  if (wsHeartbeat) clearInterval(wsHeartbeat);
  ws = new WebSocket(`ws://${location.host}/ws/echo?channel=${channel}`);
  ws.onopen = () => {
    log.textContent = `Connected to ws://${location.host}/ws/echo?channel=${channel}\nHeartbeat active every 15 seconds.`;
    wsHeartbeat = setInterval(() => {
      if (!ws || ws.readyState !== WebSocket.OPEN) return;
      const heartbeat = JSON.stringify({ event: "client_keepalive", sentAt: new Date().toISOString() });
      ws.send(heartbeat);
      log.textContent += `\nHEARTBEAT ${heartbeat}`;
    }, 15000);
  };
  ws.onmessage = event => { log.textContent += `\nRECV ${event.data}`; };
  ws.onclose = () => {
    if (wsHeartbeat) clearInterval(wsHeartbeat);
    wsHeartbeat = null;
    log.textContent += "\nClosed.";
  };
  ws.onerror = () => { log.textContent += "\nWebSocket error."; };
});

on("sendWs", "click", () => {
  const log = byId("wsLog");
  if (!ws || ws.readyState !== WebSocket.OPEN) {
    log.textContent += "\nNot connected.";
    return;
  }
  const message = byId("wsMessage").value;
  ws.send(message);
  log.textContent += `\nSEND ${message}`;
});

on("sendWsCapture", "click", async () => {
  await run("wsLog", () => {
    const body = {
      channel: byId("wsChannel").value,
      payload: readJson("wsMessage")
    };
    return request("POST", "/api/websocket/real-send", body);
  });
});

on("postRealtimeEvent", "click", async () => {
  await run("wsLog", async () => {
    const payload = readJson("wsMessage");
    const body = {
      channel: byId("wsChannel").value,
      event: payload.event || byId("wsTemplate").value,
      payload,
      transport: "http-post-event"
    };
    return request("POST", "/api/realtime/events", body);
  });
});

on("loadRealtimeEvents", "click", async () => {
  const channel = encodeURIComponent(byId("wsChannel").value);
  await run("wsLog", () => request("GET", `/api/realtime/events?channel=${channel}`));
});

on("closeWs", "click", () => {
  if (wsHeartbeat) clearInterval(wsHeartbeat);
  wsHeartbeat = null;
  if (ws) ws.close();
});

on("publishMqtt", "click", async () => {
  await run("mqttOutput", () => {
    const body = {
      clientId: byId("mqttClientId").value,
      topic: byId("mqttTopic").value,
      qos: Number(byId("mqttQos").value),
      retained: byId("mqttRetained").checked,
      payload: readJson("mqttPayload")
    };
    return request("POST", "/api/mqtt/publish", body);
  });
});

on("publishRealMqtt", "click", async () => {
  await run("mqttOutput", () => {
    const body = {
      clientId: byId("mqttClientId").value,
      topic: byId("mqttTopic").value,
      filter: byId("mqttFilter").value,
      qos: Number(byId("mqttQos").value),
      retained: byId("mqttRetained").checked,
      payload: readJson("mqttPayload")
    };
    return request("POST", "/api/mqtt/real-publish", body);
  });
});

on("startMqttSession", "click", async () => {
  await run("mqttOutput", () => {
    const body = {
      clientId: byId("mqttClientId").value,
      topic: byId("mqttTopic").value,
      filter: byId("mqttFilter").value,
      qos: Number(byId("mqttQos").value),
      retained: byId("mqttRetained").checked,
      keepaliveIntervalSeconds: 15,
      payload: readJson("mqttPayload")
    };
    return request("POST", "/api/mqtt/session/start", body);
  });
});

on("stopMqttSession", "click", async () => {
  await run("mqttOutput", () => {
    const body = { clientId: byId("mqttClientId").value };
    return request("POST", "/api/mqtt/session/stop", body);
  });
});

on("loadMqtt", "click", async () => {
  const topic = encodeURIComponent(byId("mqttTopic").value);
  await run("mqttOutput", () => request("GET", `/api/mqtt/messages?topic=${topic}`));
});

on("loadMqttByFilter", "click", async () => {
  const topicFilter = encodeURIComponent(byId("mqttFilter").value);
  await run("mqttOutput", () => request("GET", `/api/mqtt/messages?filter=${topicFilter}`));
});

on("loadMqttTopics", "click", async () => {
  await run("mqttOutput", () => request("GET", "/api/mqtt/topics"));
});

on("clearMqtt", "click", async () => {
  await run("mqttOutput", () => request("POST", "/api/mqtt/clear", {}));
});

on("grpcMethod", "change", event => {
  byId("grpcBody").value = pretty(grpcTemplates[event.target.value] || grpcTemplates.Predict);
});

function setGrpcMethod(method) {
  byId("grpcMethod").value = method;
  byId("grpcBody").value = pretty(grpcTemplates[method] || grpcTemplates.Predict);
}

function grpcRequestBody(method) {
  return { method, payload: readJson("grpcBody"), timeoutSeconds: 3 };
}

async function invokeGrpc(method, mode) {
  setGrpcMethod(method);
  const body = grpcRequestBody(method);
  if (mode === "http2") return request("POST", "/api/grpc/http2-call", body);
  return request("POST", "/api/grpc/call", body);
}

on("runGrpcMock", "click", async () => {
  await run("grpcOutput", () => {
    const method = byId("grpcMethod").value;
    return request("POST", "/api/grpc/call", grpcRequestBody(method));
  });
});

on("runGrpcCall", "click", async () => {
  await run("grpcOutput", () => {
    return request("POST", "/api/grpc/call", grpcRequestBody(byId("grpcMethod").value));
  });
});

on("runGrpcHttp2", "click", async () => {
  await run("grpcOutput", () => {
    return request("POST", "/api/grpc/http2-call", grpcRequestBody(byId("grpcMethod").value));
  });
});

document.querySelectorAll("[data-grpc-method][data-grpc-mode]").forEach(btn => {
  btn.addEventListener("click", async () => {
    await run("grpcOutput", () => invokeGrpc(btn.dataset.grpcMethod, btn.dataset.grpcMode));
  });
});

on("convertEncoding", "click", async () => {
  await run("encodingOutput", () => {
    const body = { to: byId("encodingTarget").value, records: readJson("encodingRecords") };
    return request("POST", "/api/encoding/convert", body);
  });
});

on("runTroubleTest", "click", async () => {
  await run("troubleCustomOutput", () => {
    const body = {
      status: Number(byId("troubleStatus").value),
      delayMs: Number(byId("troubleDelay").value),
      scenario: byId("troubleScenario").value
    };
    return request("POST", "/api/troubleshooting/test", body);
  });
});

on("runTlsSelfTest", "click", async () => {
  await run("troubleshootingOutput", () => request("POST", "/api/tls/self-test", {}));
});

on("simulatePostmanRun", "click", async () => {
  await run("api-docsOutput", () => {
    const body = {
      folder: byId("postmanFolder").value,
      iterations: Number(byId("postmanIterations").value)
    };
    return request("POST", "/api/postman/run", body);
  });
});

on("resetReliability", "click", async () => {
  await run("reliabilityOutput", () => request("POST", "/api/reliability/reset", {}));
});

on("simulateLoad", "click", async () => {
  await run("reliabilityOutput", () => request("POST", "/api/reliability/simulate-load", { requests: 9 }));
});

on("runMicroserviceOrder", "click", async () => {
  await run("casesOutput", () => {
    const failAt = byId("microFailAt").value;
    const body = { orderId: "ORD-DEMO-001", amount: 450000, wireCapture: true };
    if (failAt) body.failAt = failAt;
    return request("POST", "/api/microservices/orders", body);
  });
});

on("runCustomLog", "click", async () => {
  const body = {
    event: "custom.observability.event",
    severity: "info",
    service: "demo-frontend",
    message: "Mahasiswa membuat log event dari UI",
    traceId: "demo-trace-001"
  };
  await run("observabilityOutput", () => request("POST", "/api/observability/custom-log", body));
});

on("runObservabilityCapture", "click", async () => {
  await run("observabilityOutput", () => request("POST", "/api/observability/capture-scenario", {}));
});

on("sendAutomationEvent", "click", async () => {
  const body = {
    protocol: "MQTT+REST+n8n",
    event: "telemetry.workflow.completed",
    deviceId: "sensor-01",
    evidence: "n8n-workflow-run"
  };
  await run("automationOutput", () => request("POST", "/api/automation/inbox", body));
});

on("simulateWorkflowRun", "click", async () => {
  const body = {
    workflow: "telemetry-to-inbox",
    event: "telemetry.workflow.completed",
    triggerPayload: {
      deviceId: "sensor-01",
      temperature: 31.2,
      source: "mqtt-simulator"
    },
    wireCapture: true
  };
  await run("automationOutput", () => request("POST", "/api/automation/workflow-run", body));
});

on("createProjectEvent", "click", async () => {
  const body = { protocol: "MQTT+WebSocket+n8n", event: "uas.demo.executed", evidence: "screenshot+postman+automation-log", wireCapture: true };
  await run("projectOutput", () => request("POST", "/api/project/events", body));
});

on("runProjectCapture", "click", async () => {
  const body = { event: "uas.demo.executed", wireCapture: true };
  await run("projectOutput", () => request("POST", "/api/project/capture-demo", body));
});

checkHealth();
setRestDefaults();
loadProducts();
