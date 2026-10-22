document.addEventListener("DOMContentLoaded", async () => {
  const registerForm = document.querySelector("#register-form");
  const loginForm = document.querySelector("#login-form");
  const logoutButton = document.querySelector("#logout-btn");
  const logsTableBody = document.querySelector("#logs-table-body");
  let refreshPromise = null;

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

  async function refreshAccessToken() {
    if (refreshPromise) {
      return refreshPromise;
    }

    refreshPromise = (async () => {
      const refreshToken = localStorage.getItem("refresh_token");

      if (!refreshToken) {
        return false;
      }

      try {
        const response = await fetch("http://127.0.0.1:8000/api/auth/refresh", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            refresh_token: refreshToken,
          }),
        });

        if (!response.ok) {
          console.error("Falha ao renovar tokens:", response.status);
          return false;
        }

        const data = await response.json();

        if (!data.access_token || !data.refresh_token) {
          return false;
        }

        localStorage.setItem("token", data.access_token);
        localStorage.setItem("refresh_token", data.refresh_token);

        return true;
      } catch (error) {
        console.error("Erro ao renovar os tokens:", error);
        return false;
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

      return fetch(url, {
        ...options,
        headers: {
          ...options.headers,
          Authorization: `Bearer ${token}`,
        },
      });
    };

    let response = await sendRequest();

    if (response.status !== 401) {
      return response;
    }

    const refreshed = await refreshAccessToken();

    if (!refreshed) {
      localStorage.removeItem("token");
      localStorage.removeItem("refresh_token");
      localStorage.removeItem("loggedUser");

      window.location.replace("http://127.0.0.1:5500/frontend/pages/login.html");

      return response;
    }

    response = await sendRequest();

    if (response.status === 401) {
      localStorage.removeItem("token");
      localStorage.removeItem("refresh_token");
      localStorage.removeItem("loggedUser");

      window.location.replace("http://127.0.0.1:5500/frontend/pages/login.html");
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
        const response = await fetch("http://127.0.0.1:8000/api/auth/register", {
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

        const data = await response.json();

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
          window.location.assign("http://127.0.0.1:5500/frontend/pages/login.html");
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
        const response = await fetch("http://127.0.0.1:8000/api/auth/login", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            email: email,
            password: password,
          }),
        });

        const data = await response.json();

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

        localStorage.setItem("token", data.access_token);
        localStorage.setItem("refresh_token", data.refresh_token);

        console.log("Login realizado com sucesso.");

        window.location.replace("http://127.0.0.1:5500/frontend/pages/dashboard.html");
      } catch (error) {
        console.error("Erro:", error);

        showToast("Não foi possível conectar com a API.", "error");
      }
    });
  }

  if (logsTableBody) {
    const token = localStorage.getItem("token");

    let currentPage = 1;
    const limit = 10;

    const prevPageButton = document.querySelector("#prev-page");
    const nextPageButton = document.querySelector("#next-page");
    const paginationInfo = document.querySelector("#pagination-info");

    if (!token) {
      window.location.replace("http://127.0.0.1:5500/frontend/pages/login.html");
      return;
    }

    try {
      const response = await authenticatedFetch("http://127.0.0.1:8000/api/auth/me", {
        method: "GET",
      });

      const data = await response.json();

      if (!response.ok) {
        showToast(data.detail || "Sessão inválida.", "error");

        localStorage.removeItem("token");

        setTimeout(() => {
          window.location.replace("http://127.0.0.1:5500/frontend/pages/login.html");
        }, 1500);

        return;
      }

      const userEmail = document.querySelector("#user-email");

      if (userEmail) {
        userEmail.textContent = data.email;
      }

      console.log("Usuário logado:", data);

      async function loadLogs(page) {
        try {
          const logsResponse = await authenticatedFetch(`http://127.0.0.1:8000/api/auth/logs?page=${page}&limit=${limit}`, {
            method: "GET",
          });

          const logs = await logsResponse.json();

          if (logsResponse.status === 429) {
            showToast("Muitas tentativas. Aguarde um momento antes de tentar novamente.", "error");
            return;
          }

          if (!logsResponse.ok) {
            showToast(logs.detail || "Erro ao carregar histórico.", "error");
            return;
          }

          console.log("Histórico:", logs);

          logsTableBody.innerHTML = "";

          logs.items.forEach((log) => {
            const row = document.createElement("tr");

            row.classList.add("hover:bg-gray-50");

            const loginDate = new Date(`${log.login_at}Z`);

            const logoutDate = log.logout_at ? new Date(`${log.logout_at}Z`) : null;

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
            loginCell.textContent = loginDate.toLocaleString("pt-BR");

            const logoutCell = document.createElement("td");
            logoutCell.className = `px-6 py-4 ${logoutDate ? "" : "text-green-600"}`;

            logoutCell.textContent = logoutDate ? logoutDate.toLocaleString("pt-BR") : "Sessão Ativa";

            row.appendChild(userCell);
            row.appendChild(loginCell);
            row.appendChild(logoutCell);

            logsTableBody.appendChild(row);
          });

          currentPage = logs.page;

          paginationInfo.textContent = `Página ${logs.page} de ${logs.pages}`;

          prevPageButton.disabled = logs.page <= 1;
          nextPageButton.disabled = logs.page >= logs.pages;
        } catch (error) {
          console.error("Erro:", error);

          showToast("Não foi possível conectar com a API.", "error");
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
    logoutButton.addEventListener("click", async () => {
      const token = localStorage.getItem("token");

      if (!token) {
        window.location.replace("http://127.0.0.1:5500/frontend/pages/login.html");
        return;
      }

      try {
        const response = await authenticatedFetch("http://127.0.0.1:8000/api/auth/logout", {
          method: "POST",
        });

        const data = await response.json();

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
          window.location.replace("http://127.0.0.1:5500/frontend/pages/login.html");
        }, 1500);
      } catch (error) {
        console.error("Erro:", error);

        showToast("Não foi possível conectar com a API.", "error");
      }
    });
  }
});
