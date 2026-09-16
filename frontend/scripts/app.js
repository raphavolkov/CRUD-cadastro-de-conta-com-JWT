document.addEventListener("DOMContentLoaded", async () => {
  const registerForm = document.querySelector("#register-form");
  const loginForm = document.querySelector("#login-form");
  const logoutButton = document.querySelector("#logout-btn");
  const logsTableBody = document.querySelector("#logs-table-body");

  if (registerForm) {
    registerForm.addEventListener("submit", async (event) => {
      event.preventDefault();

      const name = document.getElementById("name").value.trim();
      const email = document.getElementById("email").value.trim();
      const password = document.getElementById("password").value;
      const confirmPassword = document.getElementById("confirm-password").value;

      if (!name || !email || !password || !confirmPassword) {
        alert("Preencha todos os campos.");
        return;
      }

      if (password !== confirmPassword) {
        alert("As senhas não coincidem.");
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
          alert("Muitas tentativas. aguarde um momento antes de tentar novamente");
          return;
        }

        if (!response.ok) {
          alert(data.detail || "Erro ao cadastrar usuário.");
          return;
        }

        alert("Cadastro realizado com sucesso!");

        window.location.replace("http://127.0.0.1:5500/frontend/pages/login.html");
      } catch (error) {
        console.error("Erro:", error);
        alert("Não foi possível conectar com a API.");
      }
    });
  }

  if (loginForm) {
    loginForm.addEventListener("submit", async (event) => {
      event.preventDefault();

      const email = document.querySelector("#email").value.trim();
      const password = document.querySelector("#password").value;

      if (!email || !password) {
        alert("Preencha todos os campos.");
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
          alert("Muitas tentativas. aguarde um momento antes de tentar novamente");
          return;
        }

        if (!response.ok) {
          alert(data.detail || "Email ou senha inválidos.");
          return;
        }

        localStorage.setItem("token", data.access_token);

        console.log("Login realizado com sucesso.");

        window.location.replace("http://127.0.0.1:5500/frontend/pages/dashboard.html");
      } catch (error) {
        console.error("Erro:", error);
        alert("Não foi possível conectar com a API.");
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
      const response = await fetch("http://127.0.0.1:8000/api/auth/me", {
        method: "GET",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      const data = await response.json();

      if (!response.ok) {
        alert(data.detail || "Sessão inválida.");

        localStorage.removeItem("token");

        window.location.href = "./login.html";
        return;
      }

      const userEmail = document.querySelector("#user-email");

      if (userEmail) {
        userEmail.textContent = data.email;
      }

      console.log("Usuário logado:", data);

      async function loadLogs(page) {
        try {
          const logsResponse = await fetch(`http://127.0.0.1:8000/api/auth/logs?page=${page}&limit=${limit}`, {
            method: "GET",
            headers: {
              Authorization: `Bearer ${token}`,
            },
          });

          const logs = await logsResponse.json();

          if (logsResponse.status === 429) {
            alert("Muitas tentativas. aguarde um momento antes de tentar novamente");
            return;
          }

          if (!logsResponse.ok) {
            alert(logs.detail || "Erro ao carregar histórico.");
            return;
          }

          console.log("Histórico:", logs);

          logsTableBody.innerHTML = "";

          logs.items.forEach((log) => {
            const row = document.createElement("tr");

            row.classList.add("hover:bg-gray-50");

            const loginDate = new Date(log.login_at);

            const logoutDate = log.logout_at ? new Date(log.logout_at) : null;

            row.innerHTML = `
          <td class="px-6 py-4 font-medium text-gray-900">
            <div>${log.name}</div>

            <div class="text-sm text-gray-500">
              ${log.email}
            </div>
          </td>

          <td class="px-6 py-4">
            ${loginDate.toLocaleString("pt-BR")}
          </td>

          <td class="px-6 py-4 ${logoutDate ? "" : "text-green-600"}">
            ${logoutDate ? logoutDate.toLocaleString("pt-BR") : "Sessão ativa"}
          </td>
        `;

            logsTableBody.appendChild(row);
          });

          currentPage = logs.page;

          paginationInfo.textContent = `Página ${logs.page} de ${logs.pages}`;

          prevPageButton.disabled = logs.page <= 1;

          nextPageButton.disabled = logs.page >= logs.pages;
        } catch (error) {
          console.error("Erro:", error);

          alert("Não foi possível conectar com a API.");
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

      alert("Não foi possível conectar com a API.");
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
        const response = await fetch("http://127.0.0.1:8000/api/auth/logout", {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        const data = await response.json();

        if (!response.ok) {
          console.error("Erro ao fazer logout:", data);
          alert(data.detail || "Erro ao sair da conta.");
          return;
        }

        localStorage.removeItem("token");
        localStorage.removeItem("loggedUser");

        alert("Você saiu da conta.");

        window.location.replace("http://127.0.0.1:5500/frontend/pages/login.html");
      } catch (error) {
        console.error("Erro:", error);
        alert("Não foi possível conectar com a API.");
      }
    });
  }
});
