let page = 1;
let total = 0;
const size = 10;
const message = document.querySelector("#message");
async function api(url, options = {}) {
  const response = await fetch(url, options);
  if (response.status === 204) return null;
  const body = await response.json();
  if (!response.ok) throw new Error(body.error?.message || "Request failed");
  return body;
}
function error(reason) { message.textContent = reason.message; message.className = "error"; }
async function load() {
  try {
    const query = new URLSearchParams({page: String(page), per_page: String(size)});
    const status = document.querySelector("#filter").value;
    if (status) query.set("status", status);
    const result = await api(`/api/tasks?${query}`);
    total = result.total;
    if (page > 1 && result.items.length === 0) { page -= 1; return load(); }
    const list = document.querySelector("#tasks"); list.replaceChildren();
    for (const task of result.items) {
      const row = document.createElement("article"); row.className = "task";
      const title = document.createElement("h3"); title.textContent = task.title;
      const description = document.createElement("p"); description.textContent = task.description;
      const actions = document.createElement("div"); actions.className = "task-actions";
      const select = document.createElement("select"); select.setAttribute("aria-label", `Status for ${task.title}`);
      for (const [value, label] of [["todo", "To do"], ["in_progress", "In progress"], ["done", "Done"]]) select.add(new Option(label, value));
      select.value = task.status;
      select.addEventListener("change", async () => {
        select.disabled = true;
        try { await api(`/api/tasks/${task.id}`, {method:"PATCH", headers:{"Content-Type":"application/json"}, body:JSON.stringify({status:select.value})}); await load(); }
        catch (reason) { select.value = task.status; select.disabled = false; error(reason); }
      });
      const remove = document.createElement("button"); remove.className = "delete"; remove.textContent = "Delete";
      remove.setAttribute("aria-label", `Delete ${task.title}`);
      remove.addEventListener("click", async () => {
        remove.disabled = true;
        try { await api(`/api/tasks/${task.id}`, {method:"DELETE"}); await load(); }
        catch (reason) { remove.disabled = false; error(reason); }
      });
      actions.append(select, remove); row.append(title, description, actions); list.append(row);
    }
    message.className = ""; message.textContent = total ? `${total} task${total === 1 ? "" : "s"} in this view` : "No tasks yet. Create your first task.";
    document.querySelector("#page").textContent = `Page ${page}`;
    document.querySelector("#previous").disabled = page === 1;
    document.querySelector("#next").disabled = page * size >= total;
  } catch (reason) { error(reason); }
}
document.querySelector("#create").addEventListener("submit", async event => {
  event.preventDefault(); const button = event.target.querySelector("button"); button.disabled = true;
  try {
    await api("/api/tasks", {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify(Object.fromEntries(new FormData(event.target)))});
    event.target.reset(); page = 1; document.querySelector("#filter").value = ""; await load();
  } catch (reason) { error(reason); }
  finally { button.disabled = false; }
});
document.querySelector("#filter").addEventListener("change", () => {page = 1; load();});
document.querySelector("#previous").addEventListener("click", () => {if (page > 1) {page -= 1; load();}});
document.querySelector("#next").addEventListener("click", () => {if (page * size < total) {page += 1; load();}});
load();
