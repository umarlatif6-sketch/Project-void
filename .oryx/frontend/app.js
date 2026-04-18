const API = "http://127.0.0.1:5000";

const authStatus = document.getElementById("authStatus");
const worldList = document.getElementById("worldList");
const worldState = document.getElementById("worldState");
const streamStatus = document.getElementById("streamStatus");
const collaboratorList = document.getElementById("collaboratorList");
const inviteList = document.getElementById("inviteList");
const inviteStatus = document.getElementById("inviteStatus");
const auditMeta = document.getElementById("auditMeta");
const worldSummary = document.getElementById("worldSummary");
const worldRepairState = document.getElementById("worldRepairState");
const permissionList = document.getElementById("permissionList");
const auditList = document.getElementById("auditList");
const socket = io(API, { autoConnect: false, transports: ["websocket", "polling"] });

function token() {
  return localStorage.getItem("oryx_token") || "";
}

function currentWorldId() {
  return document.getElementById("selectedWorldId").value.trim();
}

function headers() {
  const t = token();
  return {
    "Content-Type": "application/json",
    ...(t ? { Authorization: `Bearer ${t}` } : {}),
  };
}

function setStatus(text) {
  authStatus.textContent = text;
}

function setStreamStatus(text) {
  streamStatus.textContent = text;
}

function setInviteStatus(text) {
  inviteStatus.textContent = text;
}

function auditPaging() {
  const limit = Math.max(1, Number(document.getElementById("auditPageSize").value || "10"));
  const offset = Math.max(0, Number(document.getElementById("auditOffset").value || "0"));
  return { limit, offset };
}

function setAuditOffset(offset) {
  document.getElementById("auditOffset").value = String(Math.max(0, offset));
}

async function post(path, body) {
  const res = await fetch(`${API}${path}`, {
    method: "POST",
    headers: headers(),
    body: JSON.stringify(body || {}),
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.error || "Request failed");
  }
  return data;
}

async function get(path) {
  const res = await fetch(`${API}${path}`, { headers: headers() });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.error || "Request failed");
  }
  return data;
}

async function copyText(text) {
  await navigator.clipboard.writeText(text);
}

function ensureSocketConnected() {
  if (!socket.connected) {
    socket.connect();
  }
}

function setPermissionCheckboxes(permissions) {
  document.getElementById("permView").checked = !!permissions.can_view_world;
  document.getElementById("permStep").checked = !!permissions.can_step_world;
  document.getElementById("permAgents").checked = !!permissions.can_manage_agents;
  document.getElementById("permQuests").checked = !!permissions.can_manage_quests;
  document.getElementById("permStream").checked = !!permissions.can_manage_stream;
}

function permissionPayload() {
  return {
    can_view_world: document.getElementById("permView").checked,
    can_step_world: document.getElementById("permStep").checked,
    can_manage_agents: document.getElementById("permAgents").checked,
    can_manage_quests: document.getElementById("permQuests").checked,
    can_manage_stream: document.getElementById("permStream").checked,
  };
}

socket.on("connect", () => setStreamStatus("Realtime channel connected."));
socket.on("disconnect", () => setStreamStatus("Realtime channel disconnected."));
socket.on("joined_world", (event) => setStreamStatus(`Joined ${event.room} as ${event.role}`));
socket.on("left_world", (event) => setStreamStatus(`Left world ${event.world_id}`));
socket.on("stream_status", (event) => setStreamStatus(`Stream ${event.active ? "active" : "stopped"} for ${event.world_id}`));
socket.on("stream_error", (event) => setStreamStatus(event.error || "Realtime stream error."));
socket.on("world_state", async (state) => {
  worldState.textContent = JSON.stringify(state, null, 2);
  await Promise.all([refreshAudit(), refreshSummary()]);
});

async function refreshWorlds() {
  try {
    const worlds = await get("/api/worlds");
    worldList.innerHTML = "";
    worlds.forEach((item) => {
      const li = document.createElement("li");
      li.textContent = `${item.world_id} [${item.role}] (${item.created_at})`;
      li.addEventListener("click", async () => {
        document.getElementById("selectedWorldId").value = item.world_id;
        setAuditOffset(0);
        setStreamStatus(`Selected world ${item.world_id}`);
        await Promise.all([refreshCollaborators(), refreshInvites(), refreshPermissions(), refreshAudit(), refreshSummary()]);
      });
      worldList.appendChild(li);
    });
  } catch (err) {
    worldList.innerHTML = `<li>${err.message}</li>`;
  }
}

async function refreshCollaborators() {
  const worldId = currentWorldId();
  if (!worldId) {
    collaboratorList.innerHTML = "<li>Select a world first.</li>";
    return;
  }
  try {
    const collaborators = await get(`/api/worlds/${worldId}/collaborators`);
    collaboratorList.innerHTML = "";
    collaborators.forEach((item) => {
      const li = document.createElement("li");
      li.textContent = `${item.email} - ${item.role}`;
      collaboratorList.appendChild(li);
    });
  } catch (err) {
    collaboratorList.innerHTML = `<li>${err.message}</li>`;
  }
}

async function refreshPermissions() {
  const worldId = currentWorldId();
  if (!worldId) {
    permissionList.innerHTML = "<li>Select a world first.</li>";
    return;
  }
  try {
    const collaborators = await get(`/api/worlds/${worldId}/permissions`);
    permissionList.innerHTML = "";
    collaborators.forEach((item) => {
      const li = document.createElement("li");
      const perms = item.permissions || {};
      li.textContent = `${item.email} - ${item.role} - view:${perms.can_view_world} step:${perms.can_step_world} agents:${perms.can_manage_agents} quests:${perms.can_manage_quests} stream:${perms.can_manage_stream}`;
      li.addEventListener("click", () => {
        document.getElementById("permissionEmail").value = item.email;
        setPermissionCheckboxes(perms);
      });
      permissionList.appendChild(li);
    });
  } catch (err) {
    permissionList.innerHTML = `<li>${err.message}</li>`;
  }
}

async function refreshInvites() {
  const worldId = currentWorldId();
  if (!worldId) {
    inviteList.innerHTML = "<li>Select a world first.</li>";
    return;
  }
  try {
    const invites = await get(`/api/worlds/${worldId}/invites`);
    inviteList.innerHTML = "";
    invites.forEach((item) => {
      const li = document.createElement("li");
      const state = item.revoked_at ? "revoked" : item.used_at ? "used" : "active";
      li.textContent = `${item.token} - ${item.role} - expires ${item.expires_at} - ${state}${item.share_url ? ` - ${item.share_url}` : ""}`;
      li.addEventListener("click", () => {
        document.getElementById("revokeInviteToken").value = item.token;
        if (item.share_url) {
          document.getElementById("acceptInviteToken").value = item.token;
          inviteStatus.dataset.shareUrl = item.share_url;
        }
      });
      inviteList.appendChild(li);
    });
  } catch (err) {
    inviteList.innerHTML = `<li>${err.message}</li>`;
  }
}

async function refreshAudit() {
  const worldId = currentWorldId();
  if (!worldId) {
    auditList.innerHTML = "<li>Select a world first.</li>";
    auditMeta.textContent = "";
    return;
  }
  try {
    const { limit, offset } = auditPaging();
    const params = new URLSearchParams({
      limit: String(limit),
      offset: String(offset),
    });
    const action = document.getElementById("auditActionFilter").value.trim();
    const actor = document.getElementById("auditActorFilter").value.trim().toLowerCase();
    const repairState = document.getElementById("auditRepairStateFilter").value.trim().toLowerCase();
    if (action) {
      params.set("action", action);
    }
    if (actor) {
      params.set("actor_email", actor);
    }
    if (repairState) {
      params.set("repair_state", repairState);
    }
    const audit = await get(`/api/worlds/${worldId}/audit?${params.toString()}`);
    auditList.innerHTML = "";
    if (!audit.items.length) {
      auditList.innerHTML = "<li>No audit entries for the current filter.</li>";
    }
    audit.items.forEach((item) => {
      const li = document.createElement("li");
      li.textContent = `[${item.repair_state}] ${item.created_at} - ${item.actor_email || "system"} - ${item.action} - ${item.target_type}${item.target_id ? `:${item.target_id}` : ""}`;
      auditList.appendChild(li);
    });
    auditMeta.textContent = `Showing ${audit.items.length} of ${audit.total} entries (offset ${audit.offset}, limit ${audit.limit})`;
  } catch (err) {
    auditList.innerHTML = `<li>${err.message}</li>`;
    auditMeta.textContent = "";
  }
}

async function refreshSummary() {
  const worldId = currentWorldId();
  if (!worldId) {
    worldRepairState.textContent = "";
    worldSummary.textContent = "Select a world first.";
    return;
  }
  try {
    const summary = await get(`/api/worlds/${worldId}/summary`);
    const issues = (summary.issues || []).map((item) => item.code).join(", ") || "no active repair issues";
    worldRepairState.textContent = `Repair state: ${summary.repair_state} (${issues})`;
    worldSummary.textContent = JSON.stringify(summary, null, 2);
  } catch (err) {
    worldRepairState.textContent = "";
    worldSummary.textContent = err.message;
  }
}

document.getElementById("register").addEventListener("click", async () => {
  try {
    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;
    await post("/api/auth/register", { email, password });
    setStatus("Registered. Now login.");
  } catch (err) {
    setStatus(err.message);
  }
});

document.getElementById("login").addEventListener("click", async () => {
  try {
    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;
    const data = await post("/api/auth/login", { email, password });
    localStorage.setItem("oryx_token", data.token);
    setStatus("Logged in.");
    await refreshWorlds();
  } catch (err) {
    setStatus(err.message);
  }
});

document.getElementById("createWorld").addEventListener("click", async () => {
  try {
    const payload = {
      name: document.getElementById("worldName").value,
      template: document.getElementById("template").value,
      company_name: document.getElementById("companyName").value,
      integration_mode: "optional",
    };
    const data = await post("/api/worlds", payload);
    document.getElementById("selectedWorldId").value = data.world.id;
    setAuditOffset(0);
    worldState.textContent = JSON.stringify(data, null, 2);
    await Promise.all([refreshWorlds(), refreshCollaborators(), refreshInvites(), refreshPermissions(), refreshAudit(), refreshSummary()]);
  } catch (err) {
    worldState.textContent = err.message;
  }
});

document.getElementById("refreshWorlds").addEventListener("click", refreshWorlds);
document.getElementById("refreshCollaborators").addEventListener("click", refreshCollaborators);
document.getElementById("refreshInvites").addEventListener("click", refreshInvites);
document.getElementById("refreshPermissions").addEventListener("click", refreshPermissions);
document.getElementById("refreshAudit").addEventListener("click", refreshAudit);
document.getElementById("refreshSummary").addEventListener("click", refreshSummary);
document.getElementById("applyAuditPaging").addEventListener("click", refreshAudit);
document.getElementById("prevAuditPage").addEventListener("click", async () => {
  const { limit, offset } = auditPaging();
  setAuditOffset(Math.max(0, offset - limit));
  await refreshAudit();
});
document.getElementById("nextAuditPage").addEventListener("click", async () => {
  const { limit, offset } = auditPaging();
  setAuditOffset(offset + limit);
  await refreshAudit();
});
document.getElementById("clearAuditFilters").addEventListener("click", async () => {
  document.getElementById("auditActionFilter").value = "";
  document.getElementById("auditActorFilter").value = "";
  document.getElementById("auditRepairStateFilter").value = "";
  setAuditOffset(0);
  await refreshAudit();
});

document.getElementById("addCollaborator").addEventListener("click", async () => {
  try {
    const worldId = currentWorldId();
    if (!worldId) throw new Error("Select a world first.");
    const payload = {
      email: document.getElementById("collaboratorEmail").value.trim().toLowerCase(),
      role: document.getElementById("collaboratorRole").value,
    };
    await post(`/api/worlds/${worldId}/collaborators`, payload);
    await Promise.all([refreshCollaborators(), refreshPermissions(), refreshAudit(), refreshSummary()]);
  } catch (err) {
    collaboratorList.innerHTML = `<li>${err.message}</li>`;
  }
});

document.getElementById("removeCollaborator").addEventListener("click", async () => {
  try {
    const worldId = currentWorldId();
    if (!worldId) throw new Error("Select a world first.");
    const payload = { email: document.getElementById("collaboratorEmail").value.trim().toLowerCase() };
    await post(`/api/worlds/${worldId}/collaborators/remove`, payload);
    await Promise.all([refreshCollaborators(), refreshPermissions(), refreshAudit(), refreshSummary()]);
  } catch (err) {
    collaboratorList.innerHTML = `<li>${err.message}</li>`;
  }
});

document.getElementById("savePermissions").addEventListener("click", async () => {
  try {
    const worldId = currentWorldId();
    if (!worldId) throw new Error("Select a world first.");
    const email = document.getElementById("permissionEmail").value.trim().toLowerCase();
    if (!email) throw new Error("Collaborator email is required.");
    await post(`/api/worlds/${worldId}/permissions`, { email, ...permissionPayload() });
    await Promise.all([refreshPermissions(), refreshAudit(), refreshSummary()]);
  } catch (err) {
    permissionList.innerHTML = `<li>${err.message}</li>`;
  }
});

document.getElementById("createInvite").addEventListener("click", async () => {
  try {
    const worldId = currentWorldId();
    if (!worldId) throw new Error("Select a world first.");
    const data = await post(`/api/worlds/${worldId}/invites`, {
      role: document.getElementById("inviteRole").value,
      expires_in_hours: Number(document.getElementById("inviteExpiryHours").value || "72"),
    });
    document.getElementById("acceptInviteToken").value = data.token;
    document.getElementById("revokeInviteToken").value = data.token;
    inviteStatus.dataset.shareUrl = data.share_url || "";
    setInviteStatus(data.share_url ? `Invite created: ${data.share_url}` : `Invite created: ${data.token}`);
    await Promise.all([refreshInvites(), refreshAudit(), refreshSummary()]);
  } catch (err) {
    setInviteStatus(err.message);
  }
});

document.getElementById("copyInviteLink").addEventListener("click", async () => {
  try {
    const shareUrl = inviteStatus.dataset.shareUrl || "";
    if (!shareUrl) {
      throw new Error("Create or select an invite with a share URL first.");
    }
    await copyText(shareUrl);
    setInviteStatus(`Copied share URL: ${shareUrl}`);
  } catch (err) {
    setInviteStatus(err.message);
  }
});

document.getElementById("acceptInvite").addEventListener("click", async () => {
  try {
    const tokenValue = document.getElementById("acceptInviteToken").value.trim();
    const data = await post(`/api/invites/accept`, { token: tokenValue });
    setInviteStatus(`Invite accepted for ${data.world_id} as ${data.role}`);
    await refreshWorlds();
  } catch (err) {
    setInviteStatus(err.message);
  }
});

document.getElementById("revokeInvite").addEventListener("click", async () => {
  try {
    const worldId = currentWorldId();
    if (!worldId) throw new Error("Select a world first.");
    const tokenValue = document.getElementById("revokeInviteToken").value.trim();
    await post(`/api/worlds/${worldId}/invites/revoke`, { token: tokenValue });
    setInviteStatus(`Invite revoked: ${tokenValue}`);
    await Promise.all([refreshInvites(), refreshAudit(), refreshSummary()]);
  } catch (err) {
    setInviteStatus(err.message);
  }
});

document.getElementById("joinWorldRoom").addEventListener("click", () => {
  try {
    const worldId = currentWorldId();
    if (!worldId) throw new Error("Select a world first.");
    ensureSocketConnected();
    socket.emit("join_world", { world_id: worldId, token: token() });
  } catch (err) {
    setStreamStatus(err.message);
  }
});

document.getElementById("startStream").addEventListener("click", () => {
  try {
    const worldId = currentWorldId();
    if (!worldId) throw new Error("Select a world first.");
    ensureSocketConnected();
    socket.emit("start_stream", {
      world_id: worldId,
      token: token(),
      interval_ms: Number(document.getElementById("streamMs").value || "1000"),
      steps: Number(document.getElementById("streamSteps").value || "1"),
    });
  } catch (err) {
    setStreamStatus(err.message);
  }
});

document.getElementById("stopStream").addEventListener("click", () => {
  try {
    const worldId = currentWorldId();
    if (!worldId) throw new Error("Select a world first.");
    ensureSocketConnected();
    socket.emit("stop_stream", { world_id: worldId, token: token() });
    socket.emit("leave_world", { world_id: worldId });
  } catch (err) {
    setStreamStatus(err.message);
  }
});

document.getElementById("stepWorld").addEventListener("click", async () => {
  try {
    const worldId = currentWorldId();
    const steps = Number(document.getElementById("steps").value || "1");
    const data = await post(`/api/worlds/${worldId}/step`, { steps });
    worldState.textContent = JSON.stringify(data, null, 2);
    await Promise.all([refreshAudit(), refreshSummary()]);
  } catch (err) {
    worldState.textContent = err.message;
  }
});

document.getElementById("addAgent").addEventListener("click", async () => {
  try {
    const worldId = currentWorldId();
    const payload = {
      name: document.getElementById("agentName").value,
      behavior: document.getElementById("agentBehavior").value,
    };
    const data = await post(`/api/worlds/${worldId}/agents`, payload);
    worldState.textContent = JSON.stringify(data, null, 2);
    await Promise.all([refreshAudit(), refreshSummary()]);
  } catch (err) {
    worldState.textContent = err.message;
  }
});

document.getElementById("addQuest").addEventListener("click", async () => {
  try {
    const worldId = currentWorldId();
    const payload = { text: document.getElementById("questText").value };
    const data = await post(`/api/worlds/${worldId}/quests`, payload);
    worldState.textContent = JSON.stringify(data, null, 2);
    await Promise.all([refreshAudit(), refreshSummary()]);
  } catch (err) {
    worldState.textContent = err.message;
  }
});

const inviteParam = new URLSearchParams(window.location.search).get("invite");
if (inviteParam) {
  document.getElementById("acceptInviteToken").value = inviteParam;
  setInviteStatus("Invite token detected in URL. Log in and click Accept Invite.");
}

refreshWorlds();
