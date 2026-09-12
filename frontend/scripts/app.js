document.addEventListener("DOMContentLoaded", () => {
  const registerForm = document.querySelector("#register-form");
  const loginForm = document.querySelector("#login-form");
  const logoutButton = document.querySelector("#logout-btn");
  const logsTableBody = document.querySelector("#logs-table-body");

  if (registerForm) {
    registerForm.addEventListener("submit", (event) => {
      event.preventDefault();

      const name = document.querySelector("#name").value.trim();
      const email = document.querySelector("#email").value.trim();
      const password = document.querySelector("#password").value;
      const confirmPassword = document.querySelector("#confirm-password").value;

      if (!name || !email || !password || !confirmPassword) {
        alert("Preencha todos os campos.");
        return;
      }

      if (password !== confirmPassword) {
        alert("As senhas não são iguais.");
        return;
      }

      const user = {
        name: name,
        email: email,
        password: password,
      };

      localStorage.setItem("user", JSON.stringify(user));

      alert("Conta criada com sucesso!");

      window.location.href = "../pages/login.html";
    });
  }

  if (loginForm) {
    loginForm.addEventListener("submit", (event) => {
      event.preventDefault();

      const email = document.querySelector("#email").value.trim();
      const password = document.querySelector("#password").value;

      if (!email || !password) {
        alert("Preencha todos os campos.");
        return;
      }

      const savedUser = localStorage.getItem("user");

      if (!savedUser) {
        alert("Nenhuma conta cadastrada.");
        return;
      }

      const user = JSON.parse(savedUser);

      if (email !== user.email || password !== user.password) {
        alert("Email ou senha incorretos.");
        return;
      }

      const fakeToken = "token-temporario";

      localStorage.setItem("token", fakeToken);
      localStorage.setItem(
        "loggedUser",
        JSON.stringify({
          name: user.name,
          email: user.email,
        }),
      );

      alert("Login realizado com sucesso!");

      window.location.href = "../pages/dashboard.html";
    });
  }

  if (logsTableBody) {
    const token = localStorage.getItem("token");

    if (!token) {
      alert("Você precisa fazer login.");
      window.location.href = "./login.html";
      return;
    }

    const loggedUser = localStorage.getItem("loggedUser");

    if (loggedUser) {
      const user = JSON.parse(loggedUser);

      const userEmail = document.querySelector("#user-email");

      if (userEmail) {
        userEmail.textContent = user.email;
      }
    }

    // HISTÓRICO DE ACESSOS
    logsTableBody.innerHTML = `
      <tr class="border-b">
        <td class="px-6 py-4">
          Agora
        </td>

        <td class="px-6 py-4">
          Login
        </td>

        <td class="px-6 py-4 text-green-600">
          Ativo
        </td>
      </tr>

      <tr class="border-b">
        <td class="px-6 py-4">
          Ontem
        </td>

        <td class="px-6 py-4">
          Login
        </td>

        <td class="px-6 py-4 text-gray-500">
          Encerrado
        </td>
      </tr>
    `;
  }

  if (logoutButton) {
    logoutButton.addEventListener("click", () => {
      localStorage.removeItem("token");

      localStorage.removeItem("loggedUser");

      alert("Você saiu da conta.");

      window.location.href = "./login.html";
    });
  }
});
