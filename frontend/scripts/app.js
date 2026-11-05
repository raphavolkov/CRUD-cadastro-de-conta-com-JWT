document.addEventListener("DOMContentLoaded", async () => {
  const registerForm = document.querySelector("#register-form");
  const loginForm = document.querySelector("#login-form");
  const logoutButton = document.querySelector("#logout-btn");
  const logsTableBody = document.querySelector("#logs-table-body");
  let refreshPromise = null;

  const API_BASE_URL = "http://127.0.0.1:8000";

  const LOGIN_PAGE_URL = "./login.html";
  const DASHBOARD_PAGE_URL = "./dashboard.html";

  function showToast(message, type = "success") {
    let container = document.querySelector("#toast-container");

    if (!container) {
      container = document.createElement("div");
      container.id = "toast-container";
      container.className = "fixed top-4 right-4 z-50 flex flex-col gap-2";
      document.body.appendChild(container);
    }

    const colors = {
      success: "bg-green-600",
      error: "bg-red-600",
    };

    const toast = document.createElement("div");

    toast.className = `${colors[type]} text-white px-4 py-3 rounded-lg shadow-lg whitespace-pre-line transition-opacity duration-300`;
    toast.textContent = message;

    container.appendChild(toast);

    setTimeout(() => {
      toast.classList.add("opacity-0");

      setTimeout(() => {
        toast.remove();
      }, 300);
    }, 3000);
  }

  async function readJsonResponse(response) {
    try {
      return await response.json();
    } catch {
      return {};
    }
  }

  async function refreshAccessToken() {
    if (refreshPromise) {
      return refreshPromise;
    }

    refreshPromise = (async () => {
      const refreshToken = localStorage.getItem("refresh_token");

      if (!refreshToken) {
        return { success: false, invalidSession: true };
      }

      try {
        const response = await fetch(`${API_BASE_URL}/api/auth/refresh`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            refresh_token: refreshToken,
          }),
        });

        if (response.status === 401) {
          return { success: false, invalidSession: true };
        }

        if (!response.ok) {
          console.error("Falha ao renovar tokens:", response.status);

          return { success: false, invalidSession: false };
        }

        const data = await readJsonResponse(response);

        if (typeof data.access_token !== "string" || !data.access_token || typeof data.refresh_token !== "string" || !data.refresh_token) {
          console.error("Resposta inválida ao renovar tokens.");

          return { success: false, invalidSession: false };
        }

        localStorage.setItem("token", data.access_token);
        localStorage.setItem("refresh_token", data.refresh_token);

        return { success: true, invalidSession: false };
      } catch (error) {
        console.error("Erro ao renovar os tokens:", error);

        return { success: false, invalidSession: false };
      }
    })();

    try {
      return await refreshPromise;
    } finally {
      refreshPromise = null;
    }
  }

  async function authenticatedFetch(url, options = {}) {
    const sendRequest = () => {
      const token = localStorage.getItem("token");

      const headers = {
        ...options.headers,
      };

      if (token) {
        headers.Authorization = `Bearer ${token}`;
      }

      return fetch(url, {
        ...options,
        headers,
      });
    };

    const clearSession = () => {
      localStorage.removeItem("token");
      localStorage.removeItem("refresh_token");
      localStorage.removeItem("loggedUser");

      window.location.replace(LOGIN_PAGE_URL);
    };

    let response = await sendRequest();

    if (response.status !== 401) {
      return response;
    }

    const refreshResult = await refreshAccessToken();

    if (!refreshResult.success) {
      if (refreshResult.invalidSession) {
        clearSession();
        return response;
      }

      throw new Error("Não foi possível renovar a sessão temporariamente. Tente novamente.");
    }

    response = await sendRequest();

    if (response.status === 401) {
      clearSession();
    }

    return response;
  }

  if (registerForm) {
    registerForm.addEventListener("submit", async (event) => {
      event.preventDefault();

      const name = document.getElementById("name").value.trim();
      const email = document.getElementById("email").value.trim();
      const password = document.getElementById("password").value;
      const confirmPassword = document.getElementById("confirm-password").value;

      if (!name || !email || !password || !confirmPassword) {
        showToast("Preencha todos os campos.", "error");
        return;
      }

      if (password !== confirmPassword) {
        showToast("As senhas não coincidem.", "error");
        return;
      }

      try {
        const response = await fetch(`${API_BASE_URL}/api/auth/register`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            name: name,
            email: email,
            password: password,
          }),
        });

        const data = await readJsonResponse(response);

        if (response.status === 429) {
          showToast("Muitas tentativas. Aguarde um momento antes de tentar novamente.", "error");
          return;
        }

        if (!response.ok) {
          if (Array.isArray(data.detail)) {
            const mensagens = data.detail.map((item) => item.msg).join("\n");

            showToast(mensagens || "Dados inválidos.", "error");
          } else {
            showToast(data.detail || "Erro ao criar conta.", "error");
          }

          return;
        }

        showToast("Cadastro realizado com sucesso!");

        setTimeout(() => {
          window.location.assign(LOGIN_PAGE_URL);
        }, 2000);
      } catch (error) {
        console.error("Erro:", error);

        showToast("Não foi possível conectar com a API.", "error");
      }
    });
  }

  if (loginForm) {
    loginForm.addEventListener("submit", async (event) => {
      event.preventDefault();

      const email = document.querySelector("#email").value.trim();
      const password = document.querySelector("#password").value;

      if (!email || !password) {
        showToast("Preencha todos os campos.", "error");
        return;
      }

      try {
        const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            email: email,
            password: password,
          }),
        });

        const data = await readJsonResponse(response);

        if (response.status === 429) {
          showToast("Muitas tentativas. Aguarde um momento antes de tentar novamente.", "error");
          return;
        }

        if (!response.ok) {
          if (Array.isArray(data.detail)) {
            const mensagens = data.detail.map((item) => item.msg).join("\n");

            showToast(mensagens || "Dados inválidos.", "error");
          } else {
            showToast(data.detail || "Email ou senha inválidos.", "error");
          }

          return;
        }

        if (typeof data.access_token !== "string" || !data.access_token || typeof data.refresh_token !== "string" || !data.refresh_token) {
          console.error("Resposta inválida recebida no login.");

          showToast("Não foi possível concluir o login. Tente novamente.", "error");
          return;
        }

        localStorage.setItem("token", data.access_token);
        localStorage.setItem("refresh_token", data.refresh_token);

        console.log("Login realizado com sucesso.");

        window.location.replace(DASHBOARD_PAGE_URL);
      } catch (error) {
        console.error("Erro:", error);

        showToast("Não foi possível conectar com a API.", "error");
      }
    });
  }

  if (logsTableBody) {
    const token = localStorage.getItem("token");
    const refreshToken = localStorage.getItem("refresh_token");

    let currentPage = 1;
    const limit = 10;
    let totalPages = null;
    let isLoadingLogs = false;

    const prevPageButton = document.querySelector("#prev-page");
    const nextPageButton = document.querySelector("#next-page");
    const paginationInfo = document.querySelector("#pagination-info");

    if (!token && !refreshToken) {
      window.location.replace(LOGIN_PAGE_URL);
      return;
    }

    try {
      const response = await authenticatedFetch(`${API_BASE_URL}/api/auth/me`, {
        method: "GET",
      });

      const data = await readJsonResponse(response);

      if (response.status === 401) {
        return;
      }

      if (!response.ok) {
        showToast(data.detail || "Não foi possível carregar os dados do usuário.", "error");
        return;
      }

      const userEmail = document.querySelector("#user-email");

      if (userEmail) {
        userEmail.textContent = data.email;
      }

      console.log("Usuário logado:", data);

      async function loadLogs(page) {
        if (isLoadingLogs) {
          return;
        }

        isLoadingLogs = true;

        prevPageButton.disabled = true;
        nextPageButton.disabled = true;

        try {
          const logsResponse = await authenticatedFetch(`${API_BASE_URL}/api/auth/logs?page=${page}&limit=${limit}`, {
            method: "GET",
          });

          const logs = await readJsonResponse(logsResponse);

          if (logsResponse.status === 429) {
            showToast("Muitas tentativas. Aguarde um momento antes de tentar novamente.", "error");
            return;
          }

          if (!logsResponse.ok) {
            showToast(logs.detail || "Erro ao carregar histórico.", "error");
            return;
          }

          const validPagination =
            Array.isArray(logs.items) &&
            Number.isInteger(logs.page) &&
            logs.page >= 1 &&
            Number.isInteger(logs.pages) &&
            logs.pages >= 0 &&
            Number.isInteger(logs.total) &&
            logs.total >= 0 &&
            (logs.pages === 0 ? logs.total === 0 && logs.items.length === 0 : logs.page <= logs.pages);

          const validItems =
            validPagination &&
            logs.items.every(
              (log) =>
                log &&
                typeof log.name === "string" &&
                typeof log.email === "string" &&
                typeof log.login_at === "string" &&
                (log.logout_at === null || typeof log.logout_at === "string"),
            );

          if (!validItems) {
            console.error("Estrutura inválida recebida no histórico:", logs);
            showToast("Não foi possível interpretar o histórico de acessos.", "error");
            return;
          }

          logsTableBody.innerHTML = "";

          if (logs.items.length === 0) {
            const row = document.createElement("tr");
            const cell = document.createElement("td");

            cell.colSpan = 3;
            cell.className = "px-6 py-8 text-center text-gray-500";
            cell.textContent = "Nenhum acesso registrado.";

            row.appendChild(cell);
            logsTableBody.appendChild(row);
          }

          logs.items.forEach((log) => {
            const row = document.createElement("tr");

            row.classList.add("hover:bg-gray-50");

            const parseApiDate = (value) => {
              const hasTimezone = /(?:Z|[+-]\d{2}:\d{2})$/i.test(value);
              const date = new Date(hasTimezone ? value : `${value}Z`);

              return Number.isNaN(date.getTime()) ? null : date;
            };

            const loginDate = parseApiDate(log.login_at);
            const logoutDate = log.logout_at ? parseApiDate(log.logout_at) : null;

            const userCell = document.createElement("td");
            userCell.className = "px-6 py-4 font-medium text-gray-900";

            const nameDiv = document.createElement("div");
            nameDiv.textContent = log.name;

            const emailDiv = document.createElement("div");
            emailDiv.className = "text-sm text-gray-500";
            emailDiv.textContent = log.email;

            userCell.appendChild(nameDiv);
            userCell.appendChild(emailDiv);

            const loginCell = document.createElement("td");
            loginCell.className = "px-6 py-4";
            loginCell.textContent = loginDate ? loginDate.toLocaleString("pt-BR") : "Data inválida";

            const logoutCell = document.createElement("td");
            logoutCell.className = `px-6 py-4 ${log.logout_at === null ? "text-green-600" : ""}`;

            logoutCell.textContent = log.logout_at === null ? "Sessão Ativa" : logoutDate ? logoutDate.toLocaleString("pt-BR") : "Data inválida";

            row.appendChild(userCell);
            row.appendChild(loginCell);
            row.appendChild(logoutCell);

            logsTableBody.appendChild(row);
          });

          currentPage = logs.page;
          totalPages = logs.pages;

          paginationInfo.textContent = logs.pages === 0 ? "Nenhum registro" : `Página ${logs.page} de ${logs.pages}`;
        } catch (error) {
          console.error("Erro ao carregar histórico:", error);
          showToast("Não foi possível carregar o histórico de acessos.", "error");
        } finally {
          isLoadingLogs = false;

          prevPageButton.disabled = currentPage <= 1;

          nextPageButton.disabled = totalPages === null || totalPages === 0 || currentPage >= totalPages;
        }
      }

      prevPageButton.addEventListener("click", () => {
        if (currentPage > 1) {
          loadLogs(currentPage - 1);
        }
      });

      nextPageButton.addEventListener("click", () => {
        loadLogs(currentPage + 1);
      });

      loadLogs(currentPage);
    } catch (error) {
      console.error("Erro:", error);

      showToast("Não foi possível conectar com a API.", "error");
    }
  }

  if (logoutButton) {
    let isLoggingOut = false;

    logoutButton.addEventListener("click", async () => {
      if (isLoggingOut) {
        return;
      }

      const token = localStorage.getItem("token");

      if (!token) {
        window.location.replace(LOGIN_PAGE_URL);
        return;
      }

      isLoggingOut = true;
      logoutButton.disabled = true;

      try {
        const response = await authenticatedFetch(`${API_BASE_URL}/api/auth/logout`, {
          method: "POST",
        });

        const data = await readJsonResponse(response);

        if (!response.ok) {
          console.error("Erro ao fazer logout:", data);

          showToast(data.detail || "Erro ao sair da conta.", "error");

          return;
        }

        localStorage.removeItem("token");
        localStorage.removeItem("refresh_token");
        localStorage.removeItem("loggedUser");

        showToast("Você saiu da conta.");

        setTimeout(() => {
          window.location.replace(LOGIN_PAGE_URL);
        }, 1500);
      } catch (error) {
        console.error("Erro:", error);

        showToast("Não foi possível conectar com a API.", "error");
      } finally {
        if (localStorage.getItem("token")) {
          isLoggingOut = false;
          logoutButton.disabled = false;
        }
      }
    });
  }
});
